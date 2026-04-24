import json
import os
import random
from datetime import datetime, date
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ========== ТОКЕН БЕРЁМ ИЗ ПЕРЕМЕННОЙ ОКРУЖЕНИЯ ==========
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не задан! Добавьте переменную окружения в Render")

# ========== ХРАНЕНИЕ ДАННЫХ ==========
DATA_DIR = "vacation_data"
os.makedirs(DATA_DIR, exist_ok=True)


PLANS_FILE = os.path.join(DATA_DIR, "plans.json")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
PACKING_FILE = os.path.join(DATA_DIR, "packing.json")
EXPENSES_FILE = os.path.join(DATA_DIR, "expenses.json")
VACATION_DATE_FILE = os.path.join(DATA_DIR, "vacation_date.txt")

def load_data(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_key(chat_id, user_id=None):
    if user_id:
        return f"{chat_id}_{user_id}"
    return str(chat_id)

def get_vacation_date():
    if os.path.exists(VACATION_DATE_FILE):
        with open(VACATION_DATE_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return "2026-08-01"

def days_until_vacation():
    vacation_date_str = get_vacation_date()
    try:
        vacation = datetime.strptime(vacation_date_str, "%Y-%m-%d").date()
        today = date.today()
        days = (vacation - today).days
        if days < 0:
            return f"🎉 Отпуск уже идёт! Наслаждайтесь! 🎉"
        elif days == 0:
            return f"🎉 СЕГОДНЯ ОТПУСК! УРА! 🎉"
        else:
            return f"🏖️ До отпуска осталось {days} дней!"
    except:
        return "🏖️ Отпуск будет в августе!"

# ========== КОМАНДЫ БОТА ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏖️ Добро пожаловать в бот-планировщик отпуска!\n\n"
        "Введите /help для списка команд"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """📋 *Команды бота для планирования отпуска*

🏝️ *ПЛАНЫ*
/plan [дд.мм] [время] [что] - добавить план
   Пример: `/plan 15.08 14:00 пляж`
/plans - показать все планы

✅ *ЗАДАЧИ*
/task [что] - добавить задачу
/tasks - мои задачи
/task_done [номер] - отметить задачу выполненной

📦 *СБОРЫ*
/pack [вещь] - добавить в список сборов
/pack_list - показать список сборов
/pack_done [вещь] - отметить, что взяли

💰 *БЮДЖЕТ*
/expense [сумма] [что] - добавить трату
/balance - остаток бюджета
/expenses - все траты

🎲 *РАЗВЛЕЧЕНИЯ*
/idea - случайная идея
/wish [что] - добавить желание
/wishlist - список желаний

⏰ *РАЗНОЕ*
/days - дней до отпуска
/set_date [ГГГГ-ММ-ДД] - установить дату отпуска
/help - эта помощь"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def days_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(days_until_vacation())

async def add_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("❌ Формат: /plan 15.08 14:00 описание")
        return
    
    plan_date = args[0]
    plan_time = args[1]
    plan_desc = " ".join(args[2:])
    
    user_id = update.effective_user.id
    plans = load_data(PLANS_FILE)
    chat_key = get_user_key(update.effective_chat.id)
    
    if chat_key not in plans:
        plans[chat_key] = []
    
    plans[chat_key].append({
        "date": plan_date,
        "time": plan_time,
        "desc": plan_desc,
        "created_by": user_id,
        "created_at": datetime.now().isoformat()
    })
    save_data(PLANS_FILE, plans)
    
    await update.message.reply_text(f"✅ План добавлен!\n📅 {plan_date} {plan_time} — {plan_desc}")

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plans = load_data(PLANS_FILE)
    chat_key = get_user_key(update.effective_chat.id)
    
    if chat_key not in plans or not plans[chat_key]:
        await update.message.reply_text("📭 Планов пока нет. Добавьте командой /plan")
        return
    
    text = "🏝️ *Ваши планы на отпуск:*\n\n"
    for i, p in enumerate(plans[chat_key], 1):
        text += f"{i}. 📅 {p['date']} {p['time']} — {p['desc']}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Формат: /task описание задачи")
        return
    
    task_desc = " ".join(args)
    user_id = str(update.effective_user.id)
    
    tasks = load_data(TASKS_FILE)
    user_key = get_user_key(update.effective_chat.id, user_id)
    
    if user_key not in tasks:
        tasks[user_key] = []
    
    tasks[user_key].append({
        "desc": task_desc,
        "assigned_by": user_id,
        "created_at": datetime.now().isoformat(),
        "done": False
    })
    save_data(TASKS_FILE, tasks)
    
    await update.message.reply_text(f"✅ Задача добавлена!\n📝 {task_desc}")

async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = load_data(TASKS_FILE)
    user_key = get_user_key(update.effective_chat.id, str(update.effective_user.id))
    user_tasks = tasks.get(user_key, [])
    
    if not user_tasks:
        await update.message.reply_text("📭 У вас нет задач")
        return
    
    text = "📋 *Ваши задачи:*\n\n"
    for i, t in enumerate(user_tasks, 1):
        status = "✅" if t["done"] else "⏳"
        text += f"{status} {i}. {t['desc']}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def complete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Формат: /task_done [номер задачи]")
        return
    
    try:
        task_num = int(args[0]) - 1
    except:
        await update.message.reply_text("❌ Введите номер задачи")
        return
    
    tasks = load_data(TASKS_FILE)
    user_key = get_user_key(update.effective_chat.id, str(update.effective_user.id))
    
    if user_key not in tasks or task_num >= len(tasks[user_key]):
        await update.message.reply_text("❌ Задача с таким номером не найдена")
        return
    
    tasks[user_key][task_num]["done"] = True
    tasks[user_key][task_num]["completed_at"] = datetime.now().isoformat()
    save_data(TASKS_FILE, tasks)
    
    await update.message.reply_text(f"✅ Задача «{tasks[user_key][task_num]['desc']}» выполнена!")

async def add_packing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Формат: /pack [вещь]")
        return
    
    item = " ".join(args)
    packing = load_data(PACKING_FILE)
    chat_key = get_user_key(update.effective_chat.id)
    
    if chat_key not in packing:
        packing[chat_key] = []
    
    for p in packing[chat_key]:
        if p["item"] == item:
            await update.message.reply_text(f"⚠️ Вещь «{item}» уже в списке")
            return
    
    packing[chat_key].append({
        "item": item,
        "added_by": str(update.effective_user.id),
        "done": False
    })
    save_data(PACKING_FILE, packing)
    
    await update.message.reply_text(f"✅ «{item}» добавлен в список сборов!")

async def show_packing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    packing = load_data(PACKING_FILE)
    chat_key = get_user_key(update.effective_chat.id)
    
    if chat_key not in packing or not packing[chat_key]:
        await update.message.reply_text("📭 Список сборов пуст. Добавьте командой /pack")
        return
    
    text = "📦 *Список вещей в дорогу:*\n\n"
    for p in packing[chat_key]:
        status = "✅" if p["done"] else "⬜"
        text += f"{status} {p['item']}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def pack_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Формат: /pack_done [вещь]")
        return
    
    item = " ".join(args)
    packing = load_data(PACKING_FILE)
    chat_key = get_user_key(update.effective_chat.id)
    
    if chat_key not in packing:
        await update.message.reply_text("❌ Список сборов пуст")
        return
    
    found = False
    for p in packing[chat_key]:
        if p["item"] == item and not p["done"]:
            p["done"] = True
            found = True
            break
    
    if found:
        save_data(PACKING_FILE, packing)
        await update.message.reply_text(f"✅ «{item}» отмечено как собранное!")
    else:
        await update.message.reply_text(f"❌ Вещь «{item}» не найдена или уже отмечена")

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Формат: /expense [сумма] [описание]")
        return
    
    try:
        amount = float(args[0])
    except:
        await update.message.reply_text("❌ Сумма должна быть числом")
        return
    
    description = " ".join(args[1:])
    
    expenses = load_data(EXPENSES_FILE)
    chat_key = get_user_key(update.effective_chat.id)
    
    if chat_key not in expenses:
        expenses[chat_key] = []
    
    expenses[chat_key].append({
        "amount": amount,
        "description": description,
        "added_by": str(update.effective_user.id),
        "created_at": datetime.now().isoformat()
    })
    save_data(EXPENSES_FILE, expenses)
    
    await update.message.reply_text(f"💰 Добавлена трата: {amount} руб. — {description}")

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    expenses = load_data(EXPENSES_FILE)
    chat_key = get_user_key(update.effective_chat.id)
    total = sum(e["amount"] for e in expenses.get(chat_key, []))
    await update.message.reply_text(f"💰 *Общие траты:* {total:.2f} руб.", parse_mode="Markdown")

async def random_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ideas = [
        "🏖️ Пляжный волейбол", "🕯️ Романтический ужин на пляже",
        "🌅 Фотосессия на закате", "⛵ Морская прогулка",
        "💆‍♂️ Спа-день", "🍷 Дегустация вин", "🧺 Пикник",
        "🎣 Рыбалка", "🎨 Мастер-класс", "🎲 Игры на пляже",
        "🍣 Ужин с роллами", "🎢 Аквапарк", "🐬 Дельфинарий",
        "🍰 Испечь десерт", "🎆 Фейерверк", "🍹 Коктейльный вечер",
        "🔥 Костер", "🧘‍♀️ Йога на пляже"
    ]
    await update.message.reply_text(f"✨ Идея: {random.choice(ideas)}")

async def add_wish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Формат: /wish [что хотим сделать]")
        return
    
    wish = " ".join(args)
    wishes_data = load_data(os.path.join(DATA_DIR, "wishes.json"))
    chat_key = get_user_key(update.effective_chat.id)
    
    if chat_key not in wishes_data:
        wishes_data[chat_key] = []
    
    wishes_data[chat_key].append({
        "wish": wish,
        "added_by": str(update.effective_user.id)
    })
    save_data(os.path.join(DATA_DIR, "wishes.json"), wishes_data)
    
    await update.message.reply_text(f"⭐ Желание добавлено: «{wish}»")

async def show_wishes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wishes_data = load_data(os.path.join(DATA_DIR, "wishes.json"))
    chat_key = get_user_key(update.effective_chat.id)
    
    if chat_key not in wishes_data or not wishes_data[chat_key]:
        await update.message.reply_text("📭 Список желаний пуст")
        return
    
    text = "⭐ *Наши желания:*\n\n"
    for i, w in enumerate(wishes_data[chat_key], 1):
        text += f"{i}. {w['wish']}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def set_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Формат: /set_date 2026-08-15")
        return
    
    try:
        datetime.strptime(args[0], "%Y-%m-%d")
        with open(VACATION_DATE_FILE, "w", encoding='utf-8') as f:
            f.write(args[0])
        await update.message.reply_text(f"✅ Дата отпуска установлена: {args[0]}")
    except:
        await update.message.reply_text("❌ Неверный формат. Используйте ГГГГ-ММ-ДД")

# ========== ЗАПУСК ==========

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("days", days_command))
    app.add_handler(CommandHandler("plan", add_plan))
    app.add_handler(CommandHandler("plans", show_plans))
    app.add_handler(CommandHandler("task", add_task))
    app.add_handler(CommandHandler("tasks", show_tasks))
    app.add_handler(CommandHandler("task_done", complete_task))
    app.add_handler(CommandHandler("pack", add_packing))
    app.add_handler(CommandHandler("pack_list", show_packing))
    app.add_handler(CommandHandler("pack_done", pack_done))
    app.add_handler(CommandHandler("expense", add_expense))
    app.add_handler(CommandHandler("balance", show_balance))
    app.add_handler(CommandHandler("idea", random_idea))
    app.add_handler(CommandHandler("wish", add_wish))
    app.add_handler(CommandHandler("wishlist", show_wishes))
    app.add_handler(CommandHandler("set_date", set_date))
    
    print("🤖 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
