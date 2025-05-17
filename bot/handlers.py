from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ContentType

from asgiref.sync import sync_to_async
from pathlib import Path
from datetime import datetime

from bot.models import User, Branch, StudentClass, Task, StudentTaskVideo
from schoolbot.settings import MEDIA_ROOT
from bot.telegram_bot import bot

router = Router()

# --- States ---
class Register(StatesGroup):
    waiting_for_role = State()
    full_name = State()
    branch = State()
    student_class = State()
    child_login = State()

class StudentTaskStates(StatesGroup):
    choosing_task = State()
    waiting_for_video = State()

# --- Helpers ---
def get_main_menu(role: str) -> ReplyKeyboardMarkup:
    keyboard = []
    if role == "student":
        keyboard = [[KeyboardButton(text="Vazifalar")]]
    elif role in ("parent", "curator"):
        keyboard = [[KeyboardButton(text="Statistika"), KeyboardButton(text="Vazifalar")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# --- /start ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    tg_id = str(message.from_user.id)
    user_exists = await sync_to_async(User.objects.filter(username=tg_id).exists)()

    if user_exists:
        user = await sync_to_async(User.objects.get)(username=tg_id)
        kb = get_main_menu(user.role)
        await message.answer("✅ Siz allaqachon ro'yxatdan o'tgansiz.", reply_markup=kb)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍🎓 O‘quvchi", callback_data="role_student")],
        [InlineKeyboardButton(text="👨‍🏫 Kurator", callback_data="role_curator")],
        [InlineKeyboardButton(text="👪 Ota-ona", callback_data="role_parent")]
    ])
    await message.answer("Iltimos, rolingizni tanlang:", reply_markup=keyboard)
    await state.set_state(Register.waiting_for_role)

# --- Role selection ---
@router.callback_query(F.data.startswith("role_"))
async def role_chosen(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split("_")[1]
    await state.update_data(role=role)

    if role == "parent":
        await callback.message.answer("Farzandingiz loginini kiriting:")
        await state.set_state(Register.child_login)
    else:
        await callback.message.answer("Iltimos, to‘liq ismingizni kiriting:")
        await state.set_state(Register.full_name)

@router.message(Register.full_name)
async def get_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    branches = await sync_to_async(list)(Branch.objects.all())
    buttons = [[InlineKeyboardButton(text=branch.name, callback_data=f"branch_{branch.id}")] for branch in branches]
    await message.answer("Filialni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await state.set_state(Register.branch)

@router.callback_query(F.data.startswith("branch_"))
async def get_branch(callback: CallbackQuery, state: FSMContext):
    branch_id = int(callback.data.split("_")[1])
    await state.update_data(branch_id=branch_id)
    classes = await sync_to_async(list)(StudentClass.objects.filter(branch_id=branch_id))
    if not classes:
        await callback.message.answer("Bu filialga sinflar topilmadi.")
        return
    buttons = [[InlineKeyboardButton(text=cls.name, callback_data=f"class_{cls.id}")] for cls in classes]
    await callback.message.answer("Sinfni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await state.set_state(Register.student_class)

@router.callback_query(F.data.startswith("class_"))
async def complete_registration(callback: CallbackQuery, state: FSMContext):
    class_id = int(callback.data.split("_")[1])
    data = await state.get_data()
    user = await sync_to_async(User.objects.create)(
        username=str(callback.from_user.id),
        first_name=data["full_name"],
        role=data["role"],
        branch_id=data["branch_id"],
        student_class_id=class_id
    )
    kb = get_main_menu(user.role)
    await callback.message.answer("Ro'yxatdan muvaffaqiyatli o'tdingiz!", reply_markup=kb)

@router.message(Register.child_login)
async def get_child_login(message: Message, state: FSMContext):
    login = message.text
    try:
        child = await sync_to_async(lambda: User.objects.select_related('branch', 'student_class').get(username=login))()
        text = (
            f"Farzand ismi: {child.first_name}\n"
            f"Filiali: {child.branch.name}\n"
            f"Sinf: {child.student_class.name}\n"
            f"Login: <tg-spoiler>{child.username}</tg-spoiler>"
        )
        await message.answer(text)
    except User.DoesNotExist:
        await message.answer("Bunday foydalanuvchi topilmadi.")

# --- Tasks ---
@router.message(F.text == "Vazifalar")
async def show_tasks(message: Message, state: FSMContext):
    tasks = await sync_to_async(list)(Task.objects.all())
    if tasks:
        buttons = [[InlineKeyboardButton(text=f"{i+1}. {t.title}", callback_data=f"task_{t.id}")]
                   for i, t in enumerate(tasks)]
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("Vazifalarni tanlang:", reply_markup=markup)
    else:
        await message.answer("Hozircha vazifalar mavjud emas.")

@router.callback_query(F.data.startswith("task_"))
async def task_selected(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split("_")[1])
    await state.update_data(selected_task_id=task_id)
    await state.set_state(StudentTaskStates.waiting_for_video)
    task = await sync_to_async(Task.objects.get)(id=task_id)
    await callback.message.answer(
        f"✅ Siz tanlagan vazifa: *{task.title}*\n\n"
        "Iltimos, 1 daqiqadan oshmaydigan video yuboring.",
        parse_mode="Markdown"
    )

# --- Video upload ---
@router.message(StudentTaskStates.waiting_for_video, F.video | F.video_note)
async def receive_video(message: Message, state: FSMContext):
    from datetime import datetime
    from pathlib import Path
    from django.conf import settings
    from asgiref.sync import sync_to_async
    from .models import User, Task, StudentTaskVideo  # o'zingizdagi yo'l bo'yicha

    video = message.video or message.video_note
    print("📥 Video qabul qilindi")

    # --- Validatsiya ---
    if not video or video.duration > 30 or (video.file_size > 5 * 1024 * 1024):
        await message.answer("⚠️ Video talablarga javob bermaydi (maksimal 30 sekund, 5MB).")
        return

    if message.forward_date is not None or message.forward_from is not None:
        await message.answer("⚠️ Forward qilingan videolar qabul qilinmaydi.")
        return

    # --- Holatdan topshiriq ID ni olish ---
    data = await state.get_data()
    task_id = data.get("selected_task_id")
    print("🎯 Task ID:", task_id)

    try:
        # --- Telegramdan faylni yuklab olish ---
        file = await message.bot.get_file(video.file_id)
        file_bytes = await message.bot.download_file(file.file_path)

        # --- Faylni saqlash ---
        file_name = f"{message.from_user.id}_{task_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        save_path = Path(settings.MEDIA_ROOT) / "student_videos"
        save_path.mkdir(parents=True, exist_ok=True)
        file_path = save_path / file_name

        with open(file_path, "wb") as f:
            f.write(file_bytes.getvalue())

        # --- Ma'lumotlar bazasiga yozish ---
        db_user = await sync_to_async(User.objects.get)(username=str(message.from_user.id))
        task = await sync_to_async(Task.objects.get)(id=task_id)

        await sync_to_async(StudentTaskVideo.objects.create)(
            student=db_user,
            task=task,
            video_file=f"student_videos/{file_name}"
        )

        await state.clear()
        await message.answer("✅ Video muvaffaqiyatli yuborildi. Rahmat!")

    except Exception as e:
        print(f"❌ Xatolik: {e}")
        await message.answer("❌ Video yuborishda xatolik yuz berdi. Iltimos, qaytadan urinib ko‘ring.")



# --- Statistics ---
@router.message(F.text == "Statistika")
async def show_statistics(message: Message, state: FSMContext):
    user = await sync_to_async(User.objects.get)(username=str(message.from_user.id))
    if user.role == 'parent':
        text = (
            f"Farzand ismi: {user.first_name}\n"
            f"Filiali: {user.branch}\n"
            f"Sinf: {user.student_class}\n"
            f"Login: <tg-spoiler>{user.username}</tg-spoiler>"
        )
        await message.answer(text)
    elif user.role == 'curator':
        await message.answer("Bu sinfga oid statistika mavjud emas.")
    else:
        await message.answer("Sizda statistikaga kirish huquqi yo'q.")
