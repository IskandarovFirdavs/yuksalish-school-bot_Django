from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from asgiref.sync import sync_to_async
from bot.models import User, Branch, StudentClass, Task, VideoSubmission

router = Router()

class Register(StatesGroup):
    waiting_for_role = State()
    full_name = State()
    branch = State()
    student_class = State()
    child_login = State()

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    user = await sync_to_async(User.objects.filter)(username=str(tg_id))
    if await sync_to_async(user.exists)():
        await message.answer("Siz allaqachon ro'yxatdan o'tgansiz.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O‘quvchi", callback_data="role_student")],
        [InlineKeyboardButton(text="Kurator", callback_data="role_curator")],
        [InlineKeyboardButton(text="Ota-ona", callback_data="role_parent")]
    ])
    await message.answer("Rolingizni tanlang:", reply_markup=kb)
    await state.set_state(Register.waiting_for_role)

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
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Filialni tanlang:", reply_markup=markup)
    await state.set_state(Register.branch)

@router.callback_query(F.data.startswith("branch_"))
async def get_branch(callback: CallbackQuery, state: FSMContext):
    branch_id = int(callback.data.split("_")[1])
    await state.update_data(branch_id=branch_id)

    classes = await sync_to_async(list)(StudentClass.objects.filter(branch_id=branch_id))
    buttons = [[InlineKeyboardButton(text=cls.name, callback_data=f"class_{cls.id}")] for cls in classes]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("Sinfni tanlang:", reply_markup=markup)
    await state.set_state(Register.student_class)

@router.callback_query(F.data.startswith("class_"))
async def complete_registration(callback: CallbackQuery, state: FSMContext):
    class_id = int(callback.data.split("_")[1])
    data = await state.get_data()

    user = await sync_to_async(User.objects.create_user)(
        username=str(callback.from_user.id),
        password="telegram",
        first_name=data["full_name"],
        role=data["role"],
        branch_id=data["branch_id"],
        student_class_id=class_id
    )

    await callback.message.answer("Ro‘yxatdan o‘tish muvaffaqiyatli yakunlandi!")

    if user.role == "student":
        tasks = await sync_to_async(list)(Task.objects.all())
        if tasks:
            buttons = [
                [InlineKeyboardButton(text=f"{i+1}. {t.title}", callback_data=f"task_{t.id}")]
                for i, t in enumerate(tasks)
            ]
            markup = InlineKeyboardMarkup(inline_keyboard=buttons)
            await callback.message.answer("Vazifani tanlang:", reply_markup=markup)
        else:
            await callback.message.answer("Hozircha hech qanday vazifa mavjud emas.")
    elif user.role == "curator":
        await callback.message.answer("Statistika hali tayyor emas.")
    # ota-ona allaqachon tugagan oldin

@router.message(Register.child_login)
async def parent_login_check(message: Message, state: FSMContext):
    login = message.text
    try:
        user = await sync_to_async(User.objects.get)(username=login)
        await message.answer(
            f"Bola ismi: {user.first_name}\n"
            f"Filiali: {user.branch.name if user.branch else 'Noma’lum'}\n"
            f"Sinf: {user.student_class.name if user.student_class else 'Noma’lum'}"
        )
    except User.DoesNotExist:
        await message.answer("Bunday foydalanuvchi topilmadi.")

def get_main_menu(role: str) -> ReplyKeyboardMarkup:
    if role == 'student':
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Vazifalar")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    elif role == 'parent':
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Statistika"), KeyboardButton(text="Vazifalar")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    elif role == 'curator':
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Statistika"), KeyboardButton(text="Vazifalar")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    else:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
    return kb


@router.callback_query(F.data.startswith("class_"))
async def choose_class(callback: CallbackQuery, state: FSMContext):
    class_id = int(callback.data.split("_")[1])
    data = await state.get_data()

    user = User.objects.create_user(
        username=str(callback.from_user.id),
        password="telegram",
        first_name=data["full_name"],
        role=data["role"],
        branch_id=data["branch_id"],
        student_class_id=class_id
    )
    kb = get_main_menu(user.role)
    await callback.message.answer("Ro'yxatdan muvaffaqiyatli o'tdingiz!", reply_markup=kb)

    if user.role == "student":
        # Vazifalarni inline keyboard bilan ko'rsatish
        tasks = await sync_to_async(list)(Task.objects.all())
        buttons = [
            [InlineKeyboardButton(text=f"{i+1}. {t.title}", callback_data=f"task_{t.id}")]
            for i, t in enumerate(tasks)
        ]
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.answer("Vazifalardan birini tanlang:", reply_markup=markup)

    elif user.role == "curator":
        await callback.message.answer("Statistika mavjud emas.\nVazifalar uchun 'Vazifalar' tugmasini bosing.")

    elif user.role == "parent":
        await callback.message.answer("Farzandingiz loginini kiriting:")
        await state.set_state(Register.child_login)


@router.message(F.text == "Vazifalar")
async def show_tasks(message: Message, state: FSMContext):
    user = await sync_to_async(User.objects.get)(username=str(message.from_user.id))
    tasks = await sync_to_async(list)(Task.objects.all())
    buttons = [
        [InlineKeyboardButton(text=f"{i+1}. {t.title}", callback_data=f"task_{t.id}")]
        for i, t in enumerate(tasks)
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Vazifalarni tanlang:", reply_markup=markup)

@router.message(F.text == "Statistika")
async def show_statistics(message: Message, state: FSMContext):
    user = await sync_to_async(User.objects.get)(username=str(message.from_user.id))
    if user.role == 'parent':
        # Farzandining ma'lumotini ko'rsatish
        child = await sync_to_async(User.objects.get)(username__in=[user.username])  # bu yerda loginni o'zgartiring agar kerak bo'lsa
        text = (
            f"Farzand ismi: {child.first_name}\n"
            f"Filiali: {child.branch}\n"
            f"Sinf: {child.student_class}\n"
            f"Login: <tg-spoiler>{child.username}</tg-spoiler>"
        )
        await message.answer(text)
    elif user.role == 'curator':
        await message.answer("Bu sinfga oid statistika mavjud emas.")
    else:
        await message.answer("Sizda statistikaga kirish huquqi yo'q.")



@router.message(Register.child_login)
async def get_child_login(message: Message, state: FSMContext):
    login = message.text
    try:
        child = await sync_to_async(User.objects.get)(username=login)
        text = (
            f"Farzand ismi: {child.first_name}\n"
            f"Filiali: {child.branch}\n"
            f"Sinf: {child.student_class}\n"
            f"Login: <tg-spoiler>{child.username}</tg-spoiler>"
        )
        await message.answer(text)
    except User.DoesNotExist:
        await message.answer("Bunday foydalanuvchi topilmadi.")
