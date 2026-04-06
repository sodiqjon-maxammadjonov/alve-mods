"""
Multi-language support: UZ, RU, EN, TR, HI
Admin panel always in Uzbek.
"""

TEXTS = {
    "uz": {
        # General
        "choose_language":   "🌐 Tilni tanlang:",
        "language_set":      "✅ Til o'zgartirildi: O'zbek tili",
        "welcome": (
            "👋 Salom, <b>{name}</b>!\n\n"
            "🚀 Bu bot orqali eng so'nggi ilovalarni yuklab olishingiz mumkin.\n\n"
            "📱 Ilovalarni yuklab olish uchun quyidagi kanalga a'zo bo'ling."
        ),
        "main_menu":         "🏠 Asosiy menyu",
        "all_apps":          "📦 Barcha ilovalar",
        "all_apps_header":   "📦 <b>Barcha ilovalar</b> — {count} ta",
        "my_requests":       "📋 Mening yuklamalarim",
        "contact_admin":     "👨‍💻 Admin bilan bog'lanish",
        "settings":          "⚙️ Sozlamalar",
        "back":              "◀️ Orqaga",
        "cancel":            "❌ Bekor qilish",
        "close":             "✖️ Yopish",

        # Settings
        "settings_title":    "⚙️ <b>Sozlamalar</b>",
        "settings_text": (
            "⚙️ <b>Sozlamalar</b>\n\n"
            "🌐 Joriy til: <b>{lang_name}</b>\n"
            "🆔 Sizning ID: <code>{user_id}</code>"
        ),
        "change_lang_btn":   "🌐 Tilni o'zgartirish",

        # Contact admin
        "contact_admin_title": "👨‍💻 <b>Admin bilan bog'lanish</b>",
        "contact_admin_text": (
            "👨‍💻 <b>Admin bilan bog'lanish</b>\n\n"
            "Savol yoki muammoingiz bo'lsa, admin bilan bog'laning:\n\n"
            "📩 {admin_link}"
        ),
        "contact_admin_btn":   "💬 Admin bilan yozishish",

        # Downloads history
        "downloads_title":    "📋 <b>Yuklab olingan ilovalar</b>",
        "downloads_text":     "📋 <b>Yuklab olingan ilovalar</b>\n\nJami: <b>{count}</b> ta\n\n",
        "downloads_item":     "📱 <b>{name}</b> — {date}\n",

        # Subscription
        "subscribe_required": (
            "⚠️ <b>Ilovani yuklab olish uchun quyidagi kanal(lar)ga a'zo bo'ling:</b>\n\n"
            "{channels}\n\n"
            "A'zo bo'lgandan so'ng ✅ <b>Tekshirish</b> tugmasini bosing."
        ),
        "check_subscription": "✅ Tekshirish",
        "not_subscribed":     "❌ Siz hali barcha kanallarga a'zo bo'lmagansiz!\n\nIltimos, avval a'zo bo'ling.",
        "subscribed_ok":      "✅ Zo'r! Siz barcha kanallarga a'zo bo'ldingiz.",

        # App detail
        "app_caption": (
            "📱 <b>{name}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "{features}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⬇️ Yuklamalar: <b>{downloads}</b>"
        ),
        "download_btn":     "⬇️ Yuklab olish",
        "no_apps":          "📭 Hozircha ilovalar yo'q.",
        "app_not_found":    "❌ Ilova topilmadi.",

        # Download
        "downloading":       "⏳ Yuklanmoqda...",
        "download_success":  "✅ Ilova yuklandi!",
        "download_failed":   "❌ Yuklashda xatolik yuz berdi. Qayta urinib ko'ring.",
        "file_link_btn":     "🔗 Havolani ochish",

        # No requests
        "no_requests":       "📭 Siz hali hech qanday ilova yuklab olmadingiz.",

        # Search
        "search_no_results": "🔍 <b>{query}</b> bo'yicha hech narsa topilmadi.\n\n💡 Boshqa nom bilan urinib ko'ring.",
        "search_results":    "🔍 <b>{query}</b> bo'yicha {count} ta natija:",

        # Admin (always Uzbek — these keys used only in admin panel)
        "admin_menu":        "👨‍💼 Admin panel",
        "admin_apps":        "📦 Ilovalar boshqaruvi",
        "admin_channels":    "📢 Kanallar boshqaruvi",
        "admin_users":       "👥 Foydalanuvchilar",
        "admin_stats":       "📊 Statistika",
        "admin_broadcast":   "📣 Xabar yuborish",
        "admin_add_app":     "➕ Ilova qo'shish",
        "admin_add_channel": "➕ Kanal qo'shish",
        "main_menu_btn":     "🏠 Asosiy menyu",

        # Add app flow
        "ask_app_name":        "📝 <b>Ilova nomini kiriting:</b>",
        "ask_app_description": "📄 <b>Ilova haqida ma'lumot kiriting:</b>\n\nHar bir xususiyatni alohida qatorda yozing.",
        "ask_app_file": (
            "📎 <b>Endi ilovani yuboring:</b>\n\n"
            "• Faylni to'g'ridan-to'g'ri yuboring\n"
            "• Yoki maxfiy guruhga yuborib, havola yoki file_id kiriting\n\n"
            "💡 Guruh: {group}"
        ),
        "app_added":         "✅ <b>Ilova muvaffaqiyatli qo'shildi!</b>\n\n📱 <b>{name}</b>",
        "channel_post_ready":"👇 Kanal uchun tayyor post:",
        "download_channel_btn": "⬇️ Yuklab olish",

        # Add channel flow
        "ask_channel_id": (
            "📢 <b>Kanal username yoki ID sini kiriting:</b>\n\n"
            "Misol: <code>@mening_kanalim</code>\n"
            "Yoki: <code>-1001234567890</code>"
        ),
        "ask_channel_name":  "✏️ <b>Kanal uchun ko'rinadigan nom kiriting:</b>",
        "channel_found":     "✅ Kanal topildi: <b>{title}</b>\n\nEski: {ch_id}",
        "channel_added":     "✅ Kanal qo'shildi: <b>{name}</b>",
        "channel_exists":    "⚠️ Bu kanal allaqachon ro'yxatda bor.",
        "channel_invalid": (
            "❌ <b>Kanal topilmadi!</b>\n\n"
            "Iltimos quyidagilarni tekshiring:\n"
            "• Botni kanalga admin qildingizmi?\n"
            "• Username to'g'ri kiritildimi? (@ bilan)\n"
            "• Yoki to'liq ID: <code>-1001234567890</code>"
        ),
        "channel_removed":   "✅ Kanal ro'yxatdan o'chirildi.",
        "no_channels":       "📭 Hozircha kanallar yo'q.",

        # Stats
        "stats_text": (
            "📊 <b>Bot statistikasi</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👥 Jami foydalanuvchilar: <b>{users}</b>\n"
            "🆕 Bugungi yangilar: <b>{today_users}</b>\n"
            "📱 Jami ilovalar: <b>{apps}</b>\n"
            "⬇️ Jami yuklamalar: <b>{downloads}</b>\n"
            "📢 Faol kanallar: <b>{channels}</b>"
        ),

        # Broadcast
        "ask_broadcast":     "📣 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:",
        "broadcast_confirm": "📣 Xabar <b>{count}</b> ta foydalanuvchiga yuboriladi.\n\nTasdiqlaysizmi?",
        "broadcast_yes":     "✅ Ha, yuborish",
        "broadcast_no":      "❌ Bekor qilish",
        "broadcast_done":    "✅ Xabar <b>{sent}</b> ta foydalanuvchiga yuborildi. <b>{failed}</b> ta xato.",
        "broadcast_sending": "📣 Yuborilmoqda... {pct}%",

        # Errors
        "error":             "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
        "not_admin":         "❌ Siz admin emassiz.",
        "cancelled":         "❌ Bekor qilindi.",
    },

    "ru": {
        "choose_language":   "🌐 Выберите язык:",
        "language_set":      "✅ Язык изменён: Русский",
        "welcome": (
            "👋 Привет, <b>{name}</b>!\n\n"
            "🚀 Через этого бота вы можете скачивать последние приложения.\n\n"
            "📱 Для скачивания необходимо подписаться на канал(ы)."
        ),
        "main_menu":         "🏠 Главное меню",
        "all_apps":          "📦 Все приложения",
        "all_apps_header":   "📦 <b>Все приложения</b> — {count} шт.",
        "my_requests":       "📋 Мои загрузки",
        "contact_admin":     "👨‍💻 Связаться с админом",
        "settings":          "⚙️ Настройки",
        "back":              "◀️ Назад",
        "cancel":            "❌ Отмена",
        "close":             "✖️ Закрыть",
        "settings_title":    "⚙️ <b>Настройки</b>",
        "settings_text": (
            "⚙️ <b>Настройки</b>\n\n"
            "🌐 Текущий язык: <b>{lang_name}</b>\n"
            "🆔 Ваш ID: <code>{user_id}</code>"
        ),
        "change_lang_btn":   "🌐 Изменить язык",
        "contact_admin_title": "👨‍💻 <b>Связаться с админом</b>",
        "contact_admin_text": (
            "👨‍💻 <b>Связаться с админом</b>\n\n"
            "Если у вас есть вопросы или проблемы:\n\n"
            "📩 {admin_link}"
        ),
        "contact_admin_btn": "💬 Написать админу",
        "downloads_title":   "📋 <b>Загруженные приложения</b>",
        "downloads_text":    "📋 <b>Загруженные приложения</b>\n\nВсего: <b>{count}</b>\n\n",
        "downloads_item":    "📱 <b>{name}</b> — {date}\n",
        "subscribe_required": (
            "⚠️ <b>Для скачивания подпишитесь на канал(ы):</b>\n\n"
            "{channels}\n\n"
            "После подписки нажмите ✅ <b>Проверить</b>."
        ),
        "check_subscription": "✅ Проверить",
        "not_subscribed":    "❌ Вы ещё не подписались на все каналы!\n\nПожалуйста, подпишитесь сначала.",
        "subscribed_ok":     "✅ Отлично! Вы подписаны на все каналы.",
        "app_caption": (
            "📱 <b>{name}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "{features}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⬇️ Скачиваний: <b>{downloads}</b>"
        ),
        "download_btn":      "⬇️ Скачать",
        "no_apps":           "📭 Пока нет приложений.",
        "app_not_found":     "❌ Приложение не найдено.",
        "downloading":       "⏳ Загрузка...",
        "download_success":  "✅ Приложение загружено!",
        "download_failed":   "❌ Ошибка загрузки. Попробуйте снова.",
        "file_link_btn":     "🔗 Открыть ссылку",
        "no_requests":       "📭 Вы ещё ничего не скачали.",
        "search_no_results": "🔍 По запросу <b>{query}</b> ничего не найдено.\n\n💡 Попробуйте другое название.",
        "search_results":    "🔍 По запросу <b>{query}</b> найдено {count} результат(ов):",
        "admin_apps":        "📦 Управление приложениями",
        "admin_channels":    "📢 Управление каналами",
        "admin_users":       "👥 Пользователи",
        "admin_stats":       "📊 Статистика",
        "admin_broadcast":   "📣 Рассылка",
        "admin_add_app":     "➕ Добавить приложение",
        "admin_add_channel": "➕ Добавить канал",
        "main_menu_btn":     "🏠 Главное меню",
        "ask_app_name":        "📝 <b>Введите название приложения:</b>",
        "ask_app_description": "📄 <b>Введите описание приложения:</b>\n\nКаждую особенность с новой строки.",
        "ask_app_file": (
            "📎 <b>Теперь отправьте приложение:</b>\n\n"
            "• Отправьте файл напрямую\n"
            "• Или вставьте ссылку/file_id\n\n"
            "💡 Группа: {group}"
        ),
        "app_added":          "✅ <b>Приложение успешно добавлено!</b>\n\n📱 <b>{name}</b>",
        "channel_post_ready": "👇 Готовый пост для канала:",
        "download_channel_btn": "⬇️ Скачать",
        "ask_channel_id": (
            "📢 <b>Введите username или ID канала:</b>\n\n"
            "Пример: <code>@my_channel</code>\n"
            "Или: <code>-1001234567890</code>"
        ),
        "ask_channel_name":   "✏️ <b>Введите отображаемое имя канала:</b>",
        "channel_found":      "✅ Канал найден: <b>{title}</b>",
        "channel_added":      "✅ Канал добавлен: <b>{name}</b>",
        "channel_exists":     "⚠️ Этот канал уже в списке.",
        "channel_invalid": (
            "❌ <b>Канал не найден!</b>\n\n"
            "Проверьте:\n"
            "• Добавлен ли бот администратором?\n"
            "• Правильно ли введён username (с @)?\n"
            "• Или полный ID: <code>-1001234567890</code>"
        ),
        "channel_removed":    "✅ Канал удалён из списка.",
        "no_channels":        "📭 Пока нет каналов.",
        "stats_text": (
            "📊 <b>Статистика бота</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👥 Всего пользователей: <b>{users}</b>\n"
            "🆕 Сегодня новых: <b>{today_users}</b>\n"
            "📱 Всего приложений: <b>{apps}</b>\n"
            "⬇️ Всего скачиваний: <b>{downloads}</b>\n"
            "📢 Активных каналов: <b>{channels}</b>"
        ),
        "ask_broadcast":      "📣 Напишите сообщение для всех пользователей:",
        "broadcast_confirm":  "📣 Сообщение будет отправлено <b>{count}</b> пользователям.\n\nПодтверждаете?",
        "broadcast_yes":      "✅ Да, отправить",
        "broadcast_no":       "❌ Отмена",
        "broadcast_done":     "✅ Отправлено <b>{sent}</b> пользователям. <b>{failed}</b> ошибок.",
        "broadcast_sending":  "📣 Отправка... {pct}%",
        "error":              "❌ Произошла ошибка. Попробуйте снова.",
        "not_admin":          "❌ Вы не являетесь администратором.",
        "cancelled":          "❌ Отменено.",
    },

    "en": {
        "choose_language":   "🌐 Choose language:",
        "language_set":      "✅ Language changed: English",
        "welcome": (
            "👋 Hello, <b>{name}</b>!\n\n"
            "🚀 Download the latest apps through this bot.\n\n"
            "📱 You need to subscribe to the channel(s) to download."
        ),
        "main_menu":         "🏠 Main Menu",
        "all_apps":          "📦 All Apps",
        "all_apps_header":   "📦 <b>All Apps</b> — {count}",
        "my_requests":       "📋 My Downloads",
        "contact_admin":     "👨‍💻 Contact Admin",
        "settings":          "⚙️ Settings",
        "back":              "◀️ Back",
        "cancel":            "❌ Cancel",
        "close":             "✖️ Close",
        "settings_title":    "⚙️ <b>Settings</b>",
        "settings_text": (
            "⚙️ <b>Settings</b>\n\n"
            "🌐 Current language: <b>{lang_name}</b>\n"
            "🆔 Your ID: <code>{user_id}</code>"
        ),
        "change_lang_btn":   "🌐 Change Language",
        "contact_admin_title": "👨‍💻 <b>Contact Admin</b>",
        "contact_admin_text": (
            "👨‍💻 <b>Contact Admin</b>\n\n"
            "If you have any questions or issues:\n\n"
            "📩 {admin_link}"
        ),
        "contact_admin_btn": "💬 Message Admin",
        "downloads_title":   "📋 <b>Downloaded Apps</b>",
        "downloads_text":    "📋 <b>Downloaded Apps</b>\n\nTotal: <b>{count}</b>\n\n",
        "downloads_item":    "📱 <b>{name}</b> — {date}\n",
        "subscribe_required": (
            "⚠️ <b>Subscribe to the following channel(s) to download:</b>\n\n"
            "{channels}\n\n"
            "After subscribing, press ✅ <b>Check</b>."
        ),
        "check_subscription": "✅ Check",
        "not_subscribed":    "❌ You haven't subscribed to all channels yet!\n\nPlease subscribe first.",
        "subscribed_ok":     "✅ Great! You are subscribed to all channels.",
        "app_caption": (
            "📱 <b>{name}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "{features}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⬇️ Downloads: <b>{downloads}</b>"
        ),
        "download_btn":      "⬇️ Download",
        "no_apps":           "📭 No apps yet.",
        "app_not_found":     "❌ App not found.",
        "downloading":       "⏳ Downloading...",
        "download_success":  "✅ App downloaded!",
        "download_failed":   "❌ Download failed. Please try again.",
        "file_link_btn":     "🔗 Open Link",
        "no_requests":       "📭 You haven't downloaded anything yet.",
        "search_no_results": "🔍 No results for <b>{query}</b>.\n\n💡 Try a different name.",
        "search_results":    "🔍 Found {count} result(s) for <b>{query}</b>:",
        "admin_channels":    "📢 Channels Management",
        "admin_users":       "👥 Users",
        "admin_stats":       "📊 Statistics",
        "admin_broadcast":   "📣 Broadcast",
        "admin_add_app":     "➕ Add App",
        "admin_add_channel": "➕ Add Channel",
        "main_menu_btn":     "🏠 Main Menu",
        "ask_app_name":        "📝 <b>Enter the app name:</b>",
        "ask_app_description": "📄 <b>Enter app description:</b>\n\nWrite each feature on a new line.",
        "ask_app_file": (
            "📎 <b>Now send the app:</b>\n\n"
            "• Send the file directly\n"
            "• Or paste a link/file_id\n\n"
            "💡 Group: {group}"
        ),
        "app_added":          "✅ <b>App successfully added!</b>\n\n📱 <b>{name}</b>",
        "channel_post_ready": "👇 Ready post for channel:",
        "download_channel_btn": "⬇️ Download",
        "ask_channel_id": (
            "📢 <b>Enter channel username or ID:</b>\n\n"
            "Example: <code>@my_channel</code>\n"
            "Or: <code>-1001234567890</code>"
        ),
        "ask_channel_name":   "✏️ <b>Enter a display name for the channel:</b>",
        "channel_found":      "✅ Channel found: <b>{title}</b>",
        "channel_added":      "✅ Channel added: <b>{name}</b>",
        "channel_exists":     "⚠️ This channel is already in the list.",
        "channel_invalid": (
            "❌ <b>Channel not found!</b>\n\n"
            "Please check:\n"
            "• Is the bot an admin in the channel?\n"
            "• Is the username correct (with @)?\n"
            "• Or full ID: <code>-1001234567890</code>"
        ),
        "channel_removed":    "✅ Channel removed from list.",
        "no_channels":        "📭 No channels yet.",
        "stats_text": (
            "📊 <b>Bot Statistics</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👥 Total users: <b>{users}</b>\n"
            "🆕 Today new: <b>{today_users}</b>\n"
            "📱 Total apps: <b>{apps}</b>\n"
            "⬇️ Total downloads: <b>{downloads}</b>\n"
            "📢 Active channels: <b>{channels}</b>"
        ),
        "ask_broadcast":      "📣 Write a message to send to all users:",
        "broadcast_confirm":  "📣 Message will be sent to <b>{count}</b> users.\n\nConfirm?",
        "broadcast_yes":      "✅ Yes, send",
        "broadcast_no":       "❌ Cancel",
        "broadcast_done":     "✅ Sent to <b>{sent}</b> users. <b>{failed}</b> failed.",
        "broadcast_sending":  "📣 Sending... {pct}%",
        "error":              "❌ An error occurred. Please try again.",
        "not_admin":          "❌ You are not an admin.",
        "cancelled":          "❌ Cancelled.",
    },

    "tr": {
        "choose_language":   "🌐 Dil seçin:",
        "language_set":      "✅ Dil değiştirildi: Türkçe",
        "welcome": (
            "👋 Merhaba, <b>{name}</b>!\n\n"
            "🚀 Bu bot aracılığıyla en son uygulamaları indirebilirsiniz.\n\n"
            "📱 İndirmek için kanal(lar)a abone olmanız gerekiyor."
        ),
        "main_menu":         "🏠 Ana Menü",
        "all_apps":          "📦 Tüm Uygulamalar",
        "all_apps_header":   "📦 <b>Tüm Uygulamalar</b> — {count} adet",
        "my_requests":       "📋 İndirmelerim",
        "contact_admin":     "👨‍💻 Admin ile İletişim",
        "settings":          "⚙️ Ayarlar",
        "back":              "◀️ Geri",
        "cancel":            "❌ İptal",
        "close":             "✖️ Kapat",
        "settings_title":    "⚙️ <b>Ayarlar</b>",
        "settings_text": (
            "⚙️ <b>Ayarlar</b>\n\n"
            "🌐 Mevcut dil: <b>{lang_name}</b>\n"
            "🆔 ID'niz: <code>{user_id}</code>"
        ),
        "change_lang_btn":   "🌐 Dili Değiştir",
        "contact_admin_title": "👨‍💻 <b>Admin ile İletişim</b>",
        "contact_admin_text": (
            "👨‍💻 <b>Admin ile İletişim</b>\n\n"
            "Sorularınız veya sorunlarınız için:\n\n"
            "📩 {admin_link}"
        ),
        "contact_admin_btn": "💬 Admin'e Yaz",
        "downloads_title":   "📋 <b>İndirilen Uygulamalar</b>",
        "downloads_text":    "📋 <b>İndirilen Uygulamalar</b>\n\nToplam: <b>{count}</b>\n\n",
        "downloads_item":    "📱 <b>{name}</b> — {date}\n",
        "subscribe_required": (
            "⚠️ <b>İndirmek için şu kanal(lar)a abone olun:</b>\n\n"
            "{channels}\n\n"
            "Abone olduktan sonra ✅ <b>Kontrol Et</b> düğmesine basın."
        ),
        "check_subscription": "✅ Kontrol Et",
        "not_subscribed":    "❌ Henüz tüm kanallara abone olmadınız!\n\nLütfen önce abone olun.",
        "subscribed_ok":     "✅ Harika! Tüm kanallara abone oldunuz.",
        "app_caption": (
            "📱 <b>{name}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "{features}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⬇️ İndirmeler: <b>{downloads}</b>"
        ),
        "download_btn":      "⬇️ İndir",
        "no_apps":           "📭 Henüz uygulama yok.",
        "app_not_found":     "❌ Uygulama bulunamadı.",
        "downloading":       "⏳ İndiriliyor...",
        "download_success":  "✅ Uygulama indirildi!",
        "download_failed":   "❌ İndirme başarısız. Tekrar deneyin.",
        "file_link_btn":     "🔗 Bağlantıyı Aç",
        "no_requests":       "📭 Henüz hiçbir şey indirmediniz.",
        "search_no_results": "🔍 <b>{query}</b> için sonuç bulunamadı.\n\n💡 Farklı bir ad deneyin.",
        "search_results":    "🔍 <b>{query}</b> için {count} sonuç bulundu:",
        "admin_apps":        "📦 Uygulama Yönetimi",
        "admin_channels":    "📢 Kanal Yönetimi",
        "admin_users":       "👥 Kullanıcılar",
        "admin_stats":       "📊 İstatistikler",
        "admin_broadcast":   "📣 Yayın",
        "admin_add_app":     "➕ Uygulama Ekle",
        "admin_add_channel": "➕ Kanal Ekle",
        "main_menu_btn":     "🏠 Ana Menü",
        "ask_app_name":        "📝 <b>Uygulama adını girin:</b>",
        "ask_app_description": "📄 <b>Uygulama açıklamasını girin:</b>\n\nHer özelliği ayrı satıra yazın.",
        "ask_app_file": (
            "📎 <b>Şimdi uygulamayı gönderin:</b>\n\n"
            "• Dosyayı doğrudan gönderin\n"
            "• Veya link/file_id yapıştırın\n\n"
            "💡 Grup: {group}"
        ),
        "app_added":          "✅ <b>Uygulama başarıyla eklendi!</b>\n\n📱 <b>{name}</b>",
        "channel_post_ready": "👇 Kanal için hazır gönderi:",
        "download_channel_btn": "⬇️ İndir",
        "ask_channel_id": (
            "📢 <b>Kanal kullanıcı adı veya ID girin:</b>\n\n"
            "Örnek: <code>@kanal_adim</code>\n"
            "Veya: <code>-1001234567890</code>"
        ),
        "ask_channel_name":   "✏️ <b>Kanal için görünen ad girin:</b>",
        "channel_found":      "✅ Kanal bulundu: <b>{title}</b>",
        "channel_added":      "✅ Kanal eklendi: <b>{name}</b>",
        "channel_exists":     "⚠️ Bu kanal zaten listede.",
        "channel_invalid": (
            "❌ <b>Kanal bulunamadı!</b>\n\n"
            "Kontrol edin:\n"
            "• Bot kanalda admin mi?\n"
            "• Kullanıcı adı doğru mu (@ ile)?\n"
            "• Tam ID: <code>-1001234567890</code>"
        ),
        "channel_removed":    "✅ Kanal listeden kaldırıldı.",
        "no_channels":        "📭 Henüz kanal yok.",
        "stats_text": (
            "📊 <b>Bot İstatistikleri</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👥 Toplam kullanıcılar: <b>{users}</b>\n"
            "🆕 Bugün yeni: <b>{today_users}</b>\n"
            "📱 Toplam uygulamalar: <b>{apps}</b>\n"
            "⬇️ Toplam indirmeler: <b>{downloads}</b>\n"
            "📢 Aktif kanallar: <b>{channels}</b>"
        ),
        "ask_broadcast":      "📣 Tüm kullanıcılara gönderilecek mesajı yazın:",
        "broadcast_confirm":  "📣 Mesaj <b>{count}</b> kullanıcıya gönderilecek.\n\nOnaylıyor musunuz?",
        "broadcast_yes":      "✅ Evet, gönder",
        "broadcast_no":       "❌ İptal",
        "broadcast_done":     "✅ <b>{sent}</b> kullanıcıya gönderildi. <b>{failed}</b> başarısız.",
        "broadcast_sending":  "📣 Gönderiliyor... {pct}%",
        "error":              "❌ Bir hata oluştu. Tekrar deneyin.",
        "not_admin":          "❌ Admin değilsiniz.",
        "cancelled":          "❌ İptal edildi.",
    },

    "hi": {
        "choose_language":   "🌐 भाषा चुनें:",
        "language_set":      "✅ भाषा बदली: हिंदी",
        "welcome": (
            "👋 नमस्ते, <b>{name}</b>!\n\n"
            "🚀 इस बॉट के ज़रिए नवीनतम ऐप्स डाउनलोड करें।\n\n"
            "📱 डाउनलोड के लिए चैनल(ों) को सब्सक्राइब करें।"
        ),
        "main_menu":         "🏠 मुख्य मेनू",
        "all_apps":          "📦 सभी ऐप्स",
        "all_apps_header":   "📦 <b>सभी ऐप्स</b> — {count}",
        "my_requests":       "📋 मेरे डाउनलोड",
        "contact_admin":     "👨‍💻 एडमिन से संपर्क",
        "settings":          "⚙️ सेटिंग्स",
        "back":              "◀️ वापस",
        "cancel":            "❌ रद्द करें",
        "close":             "✖️ बंद करें",
        "settings_title":    "⚙️ <b>सेटिंग्स</b>",
        "settings_text": (
            "⚙️ <b>सेटिंग्स</b>\n\n"
            "🌐 वर्तमान भाषा: <b>{lang_name}</b>\n"
            "🆔 आपकी ID: <code>{user_id}</code>"
        ),
        "change_lang_btn":   "🌐 भाषा बदलें",
        "contact_admin_title": "👨‍💻 <b>एडमिन से संपर्क</b>",
        "contact_admin_text": (
            "👨‍💻 <b>एडमिन से संपर्क</b>\n\n"
            "किसी भी सवाल या समस्या के लिए:\n\n"
            "📩 {admin_link}"
        ),
        "contact_admin_btn": "💬 एडमिन को मैसेज करें",
        "downloads_title":   "📋 <b>डाउनलोड किए गए ऐप्स</b>",
        "downloads_text":    "📋 <b>डाउनलोड किए गए ऐप्स</b>\n\nकुल: <b>{count}</b>\n\n",
        "downloads_item":    "📱 <b>{name}</b> — {date}\n",
        "subscribe_required": (
            "⚠️ <b>डाउनलोड के लिए इन चैनल(ों) को सब्सक्राइब करें:</b>\n\n"
            "{channels}\n\n"
            "सब्सक्राइब करने के बाद ✅ <b>जाँचें</b> दबाएँ।"
        ),
        "check_subscription": "✅ जाँचें",
        "not_subscribed":    "❌ आपने अभी सभी चैनल सब्सक्राइब नहीं किए!\n\nपहले सब्सक्राइब करें।",
        "subscribed_ok":     "✅ बढ़िया! आप सभी चैनलों के सदस्य हैं।",
        "app_caption": (
            "📱 <b>{name}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "{features}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⬇️ डाउनलोड: <b>{downloads}</b>"
        ),
        "download_btn":      "⬇️ डाउनलोड",
        "no_apps":           "📭 अभी कोई ऐप नहीं है।",
        "app_not_found":     "❌ ऐप नहीं मिला।",
        "downloading":       "⏳ डाउनलोड हो रहा है...",
        "download_success":  "✅ ऐप डाउनलोड हुआ!",
        "download_failed":   "❌ डाउनलोड विफल। पुनः प्रयास करें।",
        "file_link_btn":     "🔗 लिंक खोलें",
        "no_requests":       "📭 आपने अभी तक कुछ भी डाउनलोड नहीं किया।",
        "search_no_results": "🔍 <b>{query}</b> के लिए कोई परिणाम नहीं मिला।\n\n💡 दूसरा नाम आज़माएं।",
        "search_results":    "🔍 <b>{query}</b> के लिए {count} परिणाम मिले:",
        "admin_apps":        "📦 ऐप प्रबंधन",
        "admin_channels":    "📢 चैनल प्रबंधन",
        "admin_users":       "👥 उपयोगकर्ता",
        "admin_stats":       "📊 आँकड़े",
        "admin_broadcast":   "📣 प्रसारण",
        "admin_add_app":     "➕ ऐप जोड़ें",
        "admin_add_channel": "➕ चैनल जोड़ें",
        "main_menu_btn":     "🏠 मुख्य मेनू",
        "ask_app_name":        "📝 <b>ऐप का नाम दर्ज करें:</b>",
        "ask_app_description": "📄 <b>ऐप का विवरण दर्ज करें:</b>\n\nहर विशेषता नई लाइन पर लिखें।",
        "ask_app_file": (
            "📎 <b>अब ऐप भेजें:</b>\n\n"
            "• फ़ाइल सीधे भेजें\n"
            "• या लिंक/file_id पेस्ट करें\n\n"
            "💡 ग्रुप: {group}"
        ),
        "app_added":          "✅ <b>ऐप सफलतापूर्वक जोड़ा गया!</b>\n\n📱 <b>{name}</b>",
        "channel_post_ready": "👇 चैनल के लिए तैयार पोस्ट:",
        "download_channel_btn": "⬇️ डाउनलोड",
        "ask_channel_id": (
            "📢 <b>चैनल username या ID दर्ज करें:</b>\n\n"
            "उदाहरण: <code>@mera_channel</code>\n"
            "या: <code>-1001234567890</code>"
        ),
        "ask_channel_name":   "✏️ <b>चैनल का प्रदर्शन नाम दर्ज करें:</b>",
        "channel_found":      "✅ चैनल मिला: <b>{title}</b>",
        "channel_added":      "✅ चैनल जोड़ा गया: <b>{name}</b>",
        "channel_exists":     "⚠️ यह चैनल पहले से सूची में है।",
        "channel_invalid": (
            "❌ <b>चैनल नहीं मिला!</b>\n\n"
            "जाँचें:\n"
            "• क्या बॉट चैनल में एडमिन है?\n"
            "• Username सही है (@ के साथ)?\n"
            "• पूर्ण ID: <code>-1001234567890</code>"
        ),
        "channel_removed":    "✅ चैनल सूची से हटाया गया।",
        "no_channels":        "📭 अभी कोई चैनल नहीं।",
        "stats_text": (
            "📊 <b>बॉट आँकड़े</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👥 कुल उपयोगकर्ता: <b>{users}</b>\n"
            "🆕 आज नए: <b>{today_users}</b>\n"
            "📱 कुल ऐप्स: <b>{apps}</b>\n"
            "⬇️ कुल डाउनलोड: <b>{downloads}</b>\n"
            "📢 सक्रिय चैनल: <b>{channels}</b>"
        ),
        "ask_broadcast":      "📣 सभी उपयोगकर्ताओं को भेजने के लिए संदेश लिखें:",
        "broadcast_confirm":  "📣 संदेश <b>{count}</b> उपयोगकर्ताओं को भेजा जाएगा।\n\nपुष्टि करें?",
        "broadcast_yes":      "✅ हाँ, भेजें",
        "broadcast_no":       "❌ रद्द करें",
        "broadcast_done":     "✅ <b>{sent}</b> को भेजा गया। <b>{failed}</b> विफल।",
        "broadcast_sending":  "📣 भेजा जा रहा है... {pct}%",
        "error":              "❌ एक त्रुटि हुई। पुनः प्रयास करें।",
        "not_admin":          "❌ आप एडमिन नहीं हैं।",
        "cancelled":          "❌ रद्द किया गया।",
    },
}


LANG_FLAGS = {
    "uz": "🇺🇿 O'zbek",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "tr": "🇹🇷 Türkçe",
    "hi": "🇮🇳 हिंदी",
}


def t(lang: str, key: str, **kwargs) -> str:
    """Get localized text. Falls back to Uzbek, then returns the key itself."""
    lang = lang if lang in TEXTS else "uz"
    text = TEXTS[lang].get(key) or TEXTS["uz"].get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text