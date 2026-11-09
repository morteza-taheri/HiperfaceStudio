# -*- coding: utf-8 -*-
"""HIPERFACE Studio - translations (English / Persian) and RTL text helpers."""
import sys

LANGS = [("en", "English"), ("fa", "فارسی")]

S = {}


def _(key, en, fa):
    S[key] = {"en": en, "fa": fa}


# ---- top bar / general
_("disconnected", "Disconnected", "متصل نیست")
_("connected_sub", "%s · %s 8%s1 · addr 0x%02X", "%s · %s 8%s1 · آدرس 0x%02X")
_("port", "Port", "پورت")
_("baud", "Baud", "باود")
_("parity", "Parity", "پریتی")
_("addr", "Addr (hex)", "آدرس (hex)")
_("code0", "Code0 (hex)", "Code0 (hex)")
_("timeout", "Margin ms", "حاشیه ms")
_("connect", "Connect", "اتصال")
_("disconnect", "Disconnect", "قطع اتصال")
_("tip_refresh", "Refresh port list", "به‌روزرسانی لیست پورت‌ها")
_("tip_help", "Help (F1)", "راهنما (F1)")
_("tip_about", "About", "درباره‌ی برنامه")
_("tip_lang", "Language", "زبان")
_("tip_theme", "Light / dark theme", "تم روشن / تیره")
_("ports_found", "%d serial port(s) found", "%d پورت سریال پیدا شد")

# ---- dashboard
_("live_position", "LIVE POSITION", "موقعیت زنده")
_("raw_lbl", "raw  %d  (0x%08X)", "خام  %d  (0x%08X)")
_("raw_none", "raw  --", "خام  --")
_("turns", "turns  %d", "دور  %d")
_("turns_none", "turns  --", "دور  --")
_("k_status", "Status", "وضعیت")
_("k_temp", "Temperature", "دما")
_("k_counter", "Counter", "شمارنده")
_("k_serial", "Serial no.", "شماره سریال")
_("ok", "OK", "سالم")
_("fault", "FAULT", "خطا")
_("cpr", "Counts / rev", "پالس در دور")
_("interval", "Interval ms", "فاصله ms")
_("live", "Live read", "خواندن زنده")
_("stop", "Stop", "توقف")
_("snapshot", "Snapshot", "اسنپ‌شات")
_("log_poll", "Log every polled frame", "ثبت فریم‌های زنده در لاگ")

# ---- tabs
_("tab_pos", "Position", "موقعیت")
_("tab_cnt", "Counter", "شمارنده")
_("tab_data", "Data fields", "فیلدهای داده")
_("tab_info", "Info & status", "اطلاعات و وضعیت")
_("tab_cfg", "Configuration", "پیکربندی")
_("tab_raw", "Raw frame", "فریم خام")
_("caution", "CAUTION", "احتیاط")

# ---- buttons
for k, en, fa in [("b_read", "Read", "خواندن"), ("b_set", "Set", "تنظیم"), ("b_inc", "Increment", "افزایش"),
                  ("b_reset", "Reset", "ریست"), ("b_store", "Store", "ذخیره"), ("b_create", "Create", "ایجاد"),
                  ("b_change", "Change", "تغییر"), ("b_run", "Run", "اجرا"), ("b_apply", "Apply", "اعمال"),
                  ("b_build", "Build", "ساخت"), ("b_write", "Write", "نوشتن"), ("b_send", "Send", "ارسال"),
                  ("b_close", "Close", "بستن"), ("b_copy_info", "Copy info", "کپی اطلاعات"),
                  ("b_stack", "Read all codes", "خواندن همه‌ی کدها"), ("b_delete", "Delete", "حذف")]:
    _(k, en, fa)

# ---- field labels
for k, en, fa in [("f_value", "Value", "مقدار"), ("f_unit", "Unit", "واحد"), ("f_channel", "Channel (hex)", "کانال (hex)"),
                  ("f_field", "Field (hex)", "فیلد (hex)"), ("f_offset", "Offset", "آفست"), ("f_length", "Length", "طول"),
                  ("f_data", "Data (hex)", "داده (hex)"), ("f_size", "Size", "اندازه"), ("f_codeidx", "Code idx", "شماره کد"),
                  ("f_codeno", "Code no.", "شماره کد"), ("f_old", "Old (hex)", "قدیم (hex)"), ("f_new", "New (hex)", "جدید (hex)"),
                  ("f_newaddr", "New addr (hex)", "آدرس جدید (hex)"), ("f_baud", "Baud", "باود"),
                  ("f_parity", "Parity", "پریتی"), ("f_timeout", "Timeout", "تایم‌اوت"), ("f_mode", "Mode", "حالت"),
                  ("f_settings", "Settings (hex)", "تنظیمات (hex)"), ("f_code0", "Code0 (hex)", "Code0 (hex)"),
                  ("f_option", "Option (hex)", "گزینه (hex)"), ("f_frame", "Frame (hex)", "فریم (hex)"),
                  ("f_readbytes", "Read bytes (0=auto)", "بایت دریافتی (0=خودکار)"),
                  ("f_access", "Access code (hex)", "کد دسترسی (hex)"), ("f_codeon", "Code on", "کد فعال"),
                  ("f_write", "Writable", "قابل نوشتن")]:
    _(k, en, fa)

# ---- command cards: (title, description)
CARDS = {
    "readpos": (("Read position", "Absolute position, 32-bit. Shown as raw counts and degrees."),
                ("خواندن موقعیت", "موقعیت مطلق 32 بیتی، به‌صورت مقدار خام و درجه.")),
    "setpos": (("Set position", "Writes a position preset. Needs Code0."),
               ("تنظیم موقعیت", "مقدار پریست موقعیت را می‌نویسد. نیازمند Code0.")),
    "setsync": (("Set position w/ sync", "Optional. Rounds to the nearest 0° sin/cos phase. Motor must be still."),
                ("تنظیم موقعیت با همگام‌سازی", "اختیاری. به نزدیک‌ترین فاز صفر گرد می‌شود. موتور باید ساکن باشد.")),
    "syncoff": (("Read sync offset", "Optional. Phase shift between absolute value and sin/cos (0..31 = 1/32 period)."),
                ("خواندن آفست همگام‌سازی", "اختیاری. اختلاف فاز 0 تا 31 بین موقعیت مطلق و سینوس/کسینوس.")),
    "analog": (("Read analog value", "Channel 48h = internal temperature."),
               ("خواندن مقدار آنالوگ", "کانال 48h همان دمای داخلی است.")),
    "temp": (("Temperature", "Shortcut: analog channel 48h, signed °C."),
             ("دما", "میانبر کانال آنالوگ 48h، بر حسب درجه سانتی‌گراد.")),
    "counter": (("Read counter", "24-bit non-volatile counter."),
                ("خواندن شمارنده", "شمارنده‌ی غیرفرار 24 بیتی.")),
    "inc": (("Increment counter", "Adds 1, then reads the new value back."),
            ("افزایش شمارنده", "یک واحد اضافه می‌کند و مقدار جدید را می‌خواند.")),
    "clr": (("Reset counter", "Clears the counter to 0. Needs Code0."),
            ("صفر کردن شمارنده", "شمارنده را صفر می‌کند. نیازمند Code0.")),
    "rdata": (("Read data", "1..128 bytes from a data field. Access code = value of the field's linked code. "
                            "Field FF = extended type label."),
              ("خواندن داده", "1 تا 128 بایت از یک فیلد داده. کد دسترسی = مقدار کد مربوط به آن فیلد. "
                              "فیلد FF همان برچسب نوع توسعه‌یافته است.")),
    "sdata": (("Store data", "Write 1..128 hex bytes. Offset + length must fit in the field. Field must be writable."),
              ("ذخیره‌ی داده", "نوشتن 1 تا 128 بایت هگز. آفست + طول باید در اندازه‌ی فیلد جا شود و فیلد قابل نوشتن باشد.")),
    "dstat": (("Data field status", "Size, linked access code, code on/off, write flag, exists."),
              ("وضعیت فیلد داده", "اندازه، کد مربوط، فعال بودن کد، مجوز نوشتن و وجود فیلد.")),
    "create": (("Create / modify data field", "Field no. must be the next free number (0, 1, 2...). Size 16..128 "
                                              "(x16). Access code = current value of the selected code, even if the "
                                              "code is switched off. Size can only change on the last field."),
               ("ایجاد / ویرایش فیلد داده", "شماره‌ی فیلد باید شماره‌ی آزاد بعدی باشد (0، 1، 2 ...). اندازه 16 تا 128 "
                                            "(مضرب 16). کد دسترسی = مقدار فعلی کد انتخاب‌شده، حتی اگر کد خاموش باشد. "
                                            "تغییر اندازه فقط برای آخرین فیلد ممکن است.")),
    "delete": (("Delete data field", "4Dh with bit 7 = 0. Only the last (highest) field can be deleted."),
               ("حذف فیلد داده", "دستور 4Dh با بیت 7 برابر 0. فقط آخرین فیلد (بیشترین شماره) قابل حذف است.")),
    "ext": (("Extended type label", "Reads data field FFh (64 bytes): designation, resolution, range, checksum."),
            ("برچسب نوع توسعه‌یافته", "خواندن فیلد FFh (64 بایت): نام، دقت، بازه و چک‌سام.")),
    "mem": (("Memory status", "Free memory and number of fields."),
            ("وضعیت حافظه", "حافظه‌ی آزاد و تعداد فیلدها.")),
    "key": (("Set access code", "Change one of the 4 access codes."),
            ("تغییر کد دسترسی", "تغییر یکی از 4 کد دسترسی.")),
    "status": (("Encoder status", "One code from the error stack (max. 4). 'Read all codes' empties the stack "
                                  "and clears the warning bit."),
               ("وضعیت انکودر", "یک کد از پشته‌ی خطا (حداکثر 4). «خواندن همه‌ی کدها» پشته را خالی و بیت هشدار را پاک می‌کند.")),
    "type": (("Type label", "UART settings, type code, memory size, option code."),
             ("برچسب نوع", "تنظیمات UART، کد نوع، حجم حافظه و کد آپشن.")),
    "serial": (("Serial no. & version", "Serial number, firmware version and date."),
               ("سریال و نسخه", "شماره سریال، نسخه‌ی فریم‌ور و تاریخ.")),
    "all": (("Read everything", "Status, type label, serial/version, memory, counter, temperature."),
            ("خواندن همه", "وضعیت، برچسب نوع، سریال، حافظه، شمارنده، دما و موقعیت.")),
    "reset": (("Encoder reset", "Software reset. Encoder sends no reply."),
              ("ریست انکودر", "ریست نرم‌افزاری. انکودر پاسخی نمی‌دهد.")),
    "addr": (("Set encoder address", "Allowed 40h..5Fh. The reply already comes from the new address."),
             ("تغییر آدرس انکودر", "محدوده‌ی 40h تا 5Fh. پاسخ از همان آدرس جدید می‌آید و برنامه سوئیچ می‌کند.")),
    "uart": (("UART settings byte builder", "Compose the settings byte used by 57h / 67h. Factory default = E4h."),
             ("سازنده‌ی بایت تنظیمات UART", "ساخت بایت تنظیمات برای 57h و 67h. پیش‌فرض کارخانه E4h است.")),
    "cfg": (("Set serial interface", "Permanent. Active after 53h reset; the app then switches the port for you."),
            ("تنظیم رابط سریال", "دائمی. بعد از ریست 53h فعال می‌شود و برنامه پورت را خودکار تغییر می‌دهد.")),
    "tmp": (("Temp. set serial interface", "Optional. Reply still uses the old settings, then the app switches "
                                           "the port. Lost on reset."),
            ("تنظیم موقت رابط سریال", "اختیاری. پاسخ با تنظیمات قبلی می‌آید و بعد برنامه پورت را عوض می‌کند. "
                                      "با ریست از بین می‌رود.")),
    "adj": (("Sensor adjustment", "Optional, implementation-specific. Check the product datasheet first."),
            ("تنظیم سنسور", "اختیاری و وابسته به مدل. ابتدا دیتاشیت را بررسی کنید.")),
    "raw": (("Send raw frame", "Type address + command + data in hex. XOR checksum is appended for you. "
                               "Address FF = broadcast."),
            ("ارسال فریم خام", "آدرس، دستور و داده را به‌صورت هگز وارد کنید. چک‌سام XOR خودکار اضافه می‌شود. "
                               "آدرس FF = ارسال همگانی.")),
}

_("raw_crc", "Append XOR checksum", "افزودن چک‌سام XOR")
_("invalid_hex", "invalid hex", "هگز نامعتبر")
_("quick", "Quick frames", "فریم‌های آماده")
_("q_pos", "Position", "موقعیت")
_("q_status", "Status", "وضعیت")
_("q_type", "Type", "نوع")
_("q_ver", "Version", "نسخه")
_("q_temp", "Temp", "دما")
_("q_cnt", "Counter", "شمارنده")

# ---- log
_("log_head", "ENCODER LOG", "لاگ انکودر")
_("show_txrx", "Show TX/RX frames", "نمایش فریم‌های TX/RX")
_("autoscroll", "Auto-scroll", "اسکرول خودکار")
_("save", "Save…", "ذخیره…")
_("copy", "Copy", "کپی")
_("clear", "Clear", "پاک کردن")
_("counts", "TX %d    RX %d    errors %d    F1 help · F5 snapshot · Ctrl+L clear log",
  "TX %d    RX %d    خطا %d    F1 راهنما · F5 اسنپ‌شات · Ctrl+L پاک کردن لاگ")
_("ready", "%s ready. Pick a COM port (or DEMO) and press Connect. Press F1 for help.",
  "%s آماده است. یک پورت COM یا DEMO را انتخاب و «اتصال» را بزنید. برای راهنما F1 را بزنید.")
_("connected_log", "Connected to %s (%s baud, 8%s1, addr 0x%02X, Code0 0x%02X)",
  "اتصال به %s برقرار شد (%s باود، 8%s1، آدرس 0x%02X، Code0 0x%02X)")
_("open_fail", "Could not open %s: %s", "باز کردن %s ناموفق بود: %s")
_("port_busy", "Port is busy or the USB-RS485 driver is stuck. Close other programs using it, unplug/replug "
               "the adapter, or disable/enable it in Device Manager.",
  "پورت مشغول است یا درایور مبدل USB-RS485 گیر کرده. برنامه‌های دیگر را ببندید، مبدل را جدا و وصل کنید "
  "یا آن را در Device Manager غیرفعال و دوباره فعال کنید.")
_("closed", "Port closed.", "پورت بسته شد.")
_("live_started", "Live read started", "خواندن زنده شروع شد")
_("live_stopped", "Live read stopped", "خواندن زنده متوقف شد")
_("failed", "%s failed: %s", "%s ناموفق بود: %s")
_("last_error", "Last error: %s", "آخرین خطا: %s")
_("need_conn", "Connect to an encoder first.", "ابتدا به انکودر متصل شوید.")
_("bad_input", "Invalid input: %s", "ورودی نامعتبر: %s")
_("bad_conn", "Invalid connection settings:\n%s", "تنظیمات اتصال نامعتبر است:\n%s")
_("copied", "Log copied to clipboard", "لاگ در کلیپ‌بورد کپی شد")
_("saved", "Log saved: %s", "لاگ ذخیره شد: %s")
_("lang_changed", "Language: English", "زبان: فارسی")
_("theme_changed", "Theme: %s", "تم: %s")
_("theme_dark", "dark", "تیره")
_("theme_light", "light", "روشن")

# ---- results
_("r_pos", "Position = %d (0x%08X) = %.2f°, turn %d", "موقعیت = %d (0x%08X) = %.2f° ، دور %d")
_("r_setpos", "Position preset written", "پریست موقعیت نوشته شد")
_("r_setsync", "Position preset with sync. Value actually used: %d (0x%08X) = %.2f°",
  "موقعیت با همگام‌سازی تنظیم شد. مقدار استفاده‌شده: %d (0x%08X) = %.2f°")
_("r_syncoff", "Sync phase offset = %d  (data %s)", "آفست فاز همگام‌سازی = %d  (داده %s)")
_("r_nodata", "Done (no data bytes in reply)", "انجام شد (پاسخ بدون داده)")
_("r_analog", "Channel 0x%02X = %d (0x%04X)", "کانال 0x%02X = %d (0x%04X)")
_("r_temp", "Temperature = %d °C (raw 0x%04X)", "دما = %d °C (خام 0x%04X)")
_("r_counter", "Counter = %d", "شمارنده = %d")
_("r_inc", "Counter incremented, new value = %d", "شمارنده افزایش یافت، مقدار جدید = %d")
_("r_clr", "Counter reset, value now = %d", "شمارنده صفر شد، مقدار فعلی = %d")
_("r_rdata", "Field 0x%02X @%d [%d B]: %s   |%s|", "فیلد 0x%02X @%d [%d B]: %s   |%s|")
_("r_sdata", "Data stored", "داده ذخیره شد")
_("r_dstat", "Field 0x%02X status = 0x%02X  (size %d B, code %s, %s, %s)",
  "وضعیت فیلد 0x%02X = 0x%02X  (اندازه %d بایت، کد %s، %s، %s)")
_("writable", "writable", "قابل نوشتن")
_("readonly", "read-only", "فقط خواندنی")
_("exists", "exists", "موجود")
_("notdef", "not defined", "تعریف نشده")
_("disabled", "disabled", "غیرفعال")
_("r_create", "Field written, status byte 0x%02X (%d B, %s, %s)", "فیلد نوشته شد، بایت وضعیت 0x%02X (%d بایت، %s، %s)")
_("r_delete", "Field 0x%02X deleted (status sent 0x%02X)", "فیلد 0x%02X حذف شد (بایت وضعیت 0x%02X)")
_("cf_delete", "Delete data field 0x%02X?\nIts data is lost. Only the last field can be deleted.",
  "فیلد داده‌ی 0x%02X حذف شود؟\nداده‌های آن از بین می‌رود. فقط آخرین فیلد قابل حذف است.")
_("yes", "Yes", "بله")
_("no", "No", "خیر")
_("r_stack", "%d code(s) read, error stack is empty now", "%d کد خوانده شد، پشته‌ی خطا اکنون خالی است")
_("warn_bit", "Warning bit set in the reply to %02Xh: the encoder has a stored warning. "
              "Use Info & status > Read all codes (50h).",
  "بیت هشدار در پاسخ دستور %02Xh فعال است: انکودر هشدار ذخیره‌شده دارد. "
  "از «اطلاعات و وضعیت» گزینه‌ی «خواندن همه‌ی کدها» (50h) را بزنید.")
_("warn_pending", "! warning", "! هشدار")
_("r_ext", "Ext. type label: %s | %s | resolution %d | range %d | selector 0x%04X | checksum 0x%02X %s",
  "برچسب نوع توسعه‌یافته: %s | %s | دقت %d | بازه %d | انتخابگر 0x%04X | چک‌سام 0x%02X %s")
_("r_ext_short", "Extended type label too short: %s", "برچسب نوع توسعه‌یافته کوتاه است: %s")
_("ext_rotary", "rotary", "دوار")
_("ext_linear", "linear", "خطی")
_("r_port_switched", "PC port switched to the stored settings: %s", "پورت کامپیوتر به تنظیمات ذخیره‌شده تغییر کرد: %s")
_("r_mem", "Free memory %d bytes, %d data field(s)", "حافظه‌ی آزاد %d بایت، %d فیلد داده")
_("r_key", "Access code %d changed to 0x%02X", "کد دسترسی %d به 0x%02X تغییر کرد")
_("r_code0_upd", "App Code0 updated to 0x%02X", "Code0 برنامه به 0x%02X به‌روز شد")
_("r_status", "Status 0x%02X: %s", "وضعیت 0x%02X: %s")
_("r_type", "Type label: UART 0x%02X (%s) | type %s | memory %d B | option 0x%02X",
  "برچسب نوع: UART 0x%02X (%s) | نوع %s | حافظه %d بایت | آپشن 0x%02X")
_("ext_type", "extended type label (FFh)", "برچسب نوع توسعه‌یافته (FFh)")
_("r_serial", "Serial: %s | Firmware: %s | Date: %s", "سریال: %s | فریم‌ور: %s | تاریخ: %s")
_("report", "encoder report", "گزارش انکودر")
_("rep_type", "Type label", "برچسب نوع")
_("rep_serial", "Serial/version", "سریال/نسخه")
_("rep_mem", "Memory", "حافظه")
_("rep_pos", "Position", "موقعیت")
_("rep_mem_val", "%d B free, %d field(s)", "%d بایت آزاد، %d فیلد")
_("r_reset", "Reset sent (no reply by design). Waited for the encoder start-up.",
  "فرمان ریست ارسال شد (طبق مستند پاسخی ندارد). منتظر راه‌اندازی انکودر ماندیم.")
_("r_addr", "Address changed. App now talks to 0x%02X", "آدرس تغییر کرد. برنامه اکنون با 0x%02X ارتباط دارد")
_("r_uart", "UART settings byte = 0x%02X (%s). Copied into the 57h and 67h fields.",
  "بایت تنظیمات UART = 0x%02X (%s). در فیلدهای 57h و 67h کپی شد.")
_("r_cfg", "Serial settings stored (echo 0x%02X). Active after Encoder reset (53h); the app will switch the port then.",
  "تنظیمات سریال ذخیره شد (echo 0x%02X). بعد از ریست انکودر (53h) فعال می‌شود و برنامه پورت را عوض می‌کند.")
_("r_tmp", "Applied (echo 0x%02X). PC port switched to %s.", "اعمال شد (echo 0x%02X). پورت کامپیوتر به %s تغییر کرد.")
_("r_adj", "Reply data: %s", "داده‌ی پاسخ: %s")
_("r_noreply", "No reply", "پاسخی دریافت نشد")
_("r_reply", "Reply %d B, checksum %s", "پاسخ %d بایت، چک‌سام %s")
_("bad", "BAD", "نادرست")
_("snap", "Snapshot: %.2f° (raw %d), status 0x%02X, temp %s", "اسنپ‌شات: %.2f° (خام %d)، وضعیت 0x%02X، دما %s")
_("snap_cmd", "Snapshot (position + status + temperature)", "اسنپ‌شات (موقعیت + وضعیت + دما)")

# ---- confirmations / validation
_("cf_setpos", "Set position to %.2f° (raw %d / 0x%08X) using %s?",
  "موقعیت روی %.2f° (خام %d / 0x%08X) با دستور %s تنظیم شود؟")
_("cf_clr", "Reset the encoder counter to 0?", "شمارنده‌ی انکودر صفر شود؟")
_("cf_sdata", "Store %d byte(s) [%s] into field 0x%02X at offset %d?",
  "%d بایت [%s] در فیلد 0x%02X از آفست %d ذخیره شود؟")
_("cf_create", "Create data field 0x%02X, %d bytes, access code %d?",
  "فیلد داده‌ی 0x%02X با اندازه‌ی %d بایت و کد دسترسی %d ایجاد شود؟")
_("cf_key", "Change access code %d from 0x%02X to 0x%02X?\nIf you forget it, you lose write access.",
  "کد دسترسی %d از 0x%02X به 0x%02X تغییر کند؟\nاگر آن را فراموش کنید، دسترسی نوشتن از دست می‌رود.")
_("cf_reset", "Send software reset (53h) to the encoder?", "فرمان ریست نرم‌افزاری (53h) به انکودر ارسال شود؟")
_("cf_addr", "Change encoder address from 0x%02X to 0x%02X?", "آدرس انکودر از 0x%02X به 0x%02X تغییر کند؟")
_("cf_cfg", "PERMANENTLY write serial settings 0x%02X\n(%s)?\n\nTakes effect after reset or power cycle. "
            "You will need to reconnect with matching settings.",
  "تنظیمات سریال 0x%02X\n(%s)\nبه‌صورت دائمی نوشته شود؟\n\nپس از ریست یا قطع و وصل برق اعمال می‌شود "
  "و باید با تنظیمات جدید دوباره متصل شوید.")
_("cf_tmp", "Temporarily apply serial settings 0x%02X (%s)?\nOptional command; reverts on reset.",
  "تنظیمات سریال 0x%02X (%s) موقتاً اعمال شود؟\nدستور اختیاری است و با ریست برمی‌گردد.")
_("cf_adj", "Sensor adjustment (6Bh) is optional and implementation-specific.\n"
            "Confirm your encoder's datasheet supports option 0x%02X. Continue?",
  "دستور Sensor Adjustment (6Bh) اختیاری و وابسته به مدل است.\n"
  "مطمئن شوید دیتاشیت انکودر گزینه‌ی 0x%02X را پشتیبانی می‌کند. ادامه می‌دهید؟")
_("e_len", "length must be 1..128 bytes per request", "طول باید بین 1 تا 128 بایت باشد")
_("e_data", "data must be 1..128 bytes", "داده باید بین 1 تا 128 بایت باشد")
_("e_addr", "address must be 40h..5Fh", "آدرس باید بین 40h و 5Fh باشد")
_("e_empty", "empty frame", "فریم خالی است")
_("e_range", "address must be 40..5F (or FF = broadcast), Code0 00..FF",
  "آدرس باید بین 40 تا 5F (یا FF برای همگانی) و Code0 بین 00 تا FF باشد")

# ---- help / about windows
_("help_title", "Help", "راهنما")
_("contents", "CONTENTS", "فهرست")
_("open_pdf", "Open HIPERFACE specification (PDF)", "باز کردن مستند HIPERFACE (PDF)")
_("open_online", "Online version", "نسخه‌ی آنلاین")
_("pdf_missing", "The specification PDF was not found.\n\nExpected file name:\n%s\n\nin the program folder or in\n%s\n\n"
                 "Open the online version from sick.com instead?",
  "فایل PDF مستند پیدا نشد.\n\nنام فایل مورد انتظار:\n%s\n\nدر پوشه‌ی برنامه یا در\n%s\n\nنسخه‌ی آنلاین از سایت sick.com باز شود؟")
_("pdf_local", "Local PDF:", "PDF محلی:")
_("pdf_expected", "Project-root path:", "مسیر ریشه‌ی پروژه:")
_("browse_pdf", "Choose PDF file…", "انتخاب فایل PDF…")
_("a_issues", "Issues", "گزارش مشکل")
_("a_pdf", "Specification PDF", "PDF مستند")
_("a_pdf_online", "not found locally, opens sick.com", "به‌صورت محلی پیدا نشد، از sick.com باز می‌شود")
_("a_font", "Persian font", "فونت فارسی")
_("a_font_missing", "Vazirmatn not found, using %s (click for download page)",
  "فونت وزیر پیدا نشد، از %s استفاده می‌شود (برای دانلود کلیک کنید)")
_("a_font_src", "Vazirmatn font", "فونت وزیر")
_("pdf_found", "Local PDF: %s", "PDF محلی: %s")
_("pdf_notfound", "Local PDF not found, the online version will be used", "PDF محلی پیدا نشد، نسخه‌ی آنلاین باز می‌شود")
_("about_title", "About", "درباره")
_("about_desc", "Desktop terminal for SICK HIPERFACE® motor feedback encoders over RS-485. Every protocol command "
                "has its own form, every frame lands in the log, and a simulated encoder lets you try it all "
                "without hardware.",
  "ترمینال دسکتاپ برای انکودرهای فیدبک موتور SICK HIPERFACE® روی RS-485. هر دستور پروتکل فرم مخصوص خودش "
  "را دارد، همه‌ی فریم‌ها در لاگ ثبت می‌شوند و با انکودر شبیه‌سازی‌شده بدون سخت‌افزار هم می‌شود همه چیز را امتحان کرد.")
_("a_version", "Version", "نسخه")
_("a_author", "Developer", "توسعه‌دهنده")
_("a_email", "Email", "ایمیل")
_("a_repo", "Repository", "ریپازیتوری")
_("a_protocol", "Protocol", "پروتکل")
_("a_protocol_val", "SICK HIPERFACE® specification (IM0064865)", "مستند SICK HIPERFACE® (IM0064865)")
_("a_built", "Built with", "ساخته‌شده با")
_("a_platform", "Platform", "سیستم")
_("a_tm", "HIPERFACE® is a registered trademark of SICK STEGMANN GmbH. This tool is not affiliated with SICK.",
  "HIPERFACE® علامت تجاری ثبت‌شده‌ی SICK STEGMANN GmbH است. این برنامه وابسته به شرکت SICK نیست.")
_("info_copied", "Info copied", "اطلاعات کپی شد")


# =============================================================================
#  RTL helpers
#  Windows: GDI/Uniscribe shapes Persian itself; we only add an RTL embedding
#           so mixed Persian/Latin lines keep the right order.
#  Other OS (Tk does not shape there): minimal reshaper + visual reordering.
# =============================================================================
def is_arabic(ch):
    o = ord(ch)
    return 0x0600 <= o <= 0x06FF or 0xFB50 <= o <= 0xFDFF or 0xFE70 <= o <= 0xFEFF


def has_arabic(s):
    return any(is_arabic(c) for c in s)


_F = {  # char: (isolated, final, initial, medial); None = does not join forward
    "\u0621": (0xFE80, 0xFE80, None, None), "\u0622": (0xFE81, 0xFE82, None, None),
    "\u0623": (0xFE83, 0xFE84, None, None), "\u0624": (0xFE85, 0xFE86, None, None),
    "\u0625": (0xFE87, 0xFE88, None, None), "\u0626": (0xFE89, 0xFE8A, 0xFE8B, 0xFE8C),
    "\u0627": (0xFE8D, 0xFE8E, None, None), "\u0628": (0xFE8F, 0xFE90, 0xFE91, 0xFE92),
    "\u0629": (0xFE93, 0xFE94, None, None), "\u062A": (0xFE95, 0xFE96, 0xFE97, 0xFE98),
    "\u062B": (0xFE99, 0xFE9A, 0xFE9B, 0xFE9C), "\u062C": (0xFE9D, 0xFE9E, 0xFE9F, 0xFEA0),
    "\u062D": (0xFEA1, 0xFEA2, 0xFEA3, 0xFEA4), "\u062E": (0xFEA5, 0xFEA6, 0xFEA7, 0xFEA8),
    "\u062F": (0xFEA9, 0xFEAA, None, None), "\u0630": (0xFEAB, 0xFEAC, None, None),
    "\u0631": (0xFEAD, 0xFEAE, None, None), "\u0632": (0xFEAF, 0xFEB0, None, None),
    "\u0633": (0xFEB1, 0xFEB2, 0xFEB3, 0xFEB4), "\u0634": (0xFEB5, 0xFEB6, 0xFEB7, 0xFEB8),
    "\u0635": (0xFEB9, 0xFEBA, 0xFEBB, 0xFEBC), "\u0636": (0xFEBD, 0xFEBE, 0xFEBF, 0xFEC0),
    "\u0637": (0xFEC1, 0xFEC2, 0xFEC3, 0xFEC4), "\u0638": (0xFEC5, 0xFEC6, 0xFEC7, 0xFEC8),
    "\u0639": (0xFEC9, 0xFECA, 0xFECB, 0xFECC), "\u063A": (0xFECD, 0xFECE, 0xFECF, 0xFED0),
    "\u0641": (0xFED1, 0xFED2, 0xFED3, 0xFED4), "\u0642": (0xFED5, 0xFED6, 0xFED7, 0xFED8),
    "\u0643": (0xFED9, 0xFEDA, 0xFEDB, 0xFEDC), "\u0644": (0xFEDD, 0xFEDE, 0xFEDF, 0xFEE0),
    "\u0645": (0xFEE1, 0xFEE2, 0xFEE3, 0xFEE4), "\u0646": (0xFEE5, 0xFEE6, 0xFEE7, 0xFEE8),
    "\u0647": (0xFEE9, 0xFEEA, 0xFEEB, 0xFEEC), "\u0648": (0xFEED, 0xFEEE, None, None),
    "\u0649": (0xFEEF, 0xFEF0, None, None), "\u064A": (0xFEF1, 0xFEF2, 0xFEF3, 0xFEF4),
    "\u067E": (0xFB56, 0xFB57, 0xFB58, 0xFB59), "\u0686": (0xFB7A, 0xFB7B, 0xFB7C, 0xFB7D),
    "\u0698": (0xFB8A, 0xFB8B, None, None), "\u06A9": (0xFB8E, 0xFB8F, 0xFB90, 0xFB91),
    "\u06AF": (0xFB92, 0xFB93, 0xFB94, 0xFB95), "\u06CC": (0xFBFC, 0xFBFD, 0xFBFE, 0xFBFF),
}
_LAM_ALEF = {"\u0627": (0xFEFB, 0xFEFC), "\u0622": (0xFEF5, 0xFEF6),
             "\u0623": (0xFEF7, 0xFEF8), "\u0625": (0xFEF9, 0xFEFA)}
_MIRROR = {"(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{", "<": ">", ">": "<", "«": "»", "»": "«"}


def _shape(s):
    out = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch not in _F:
            if ch != "\u200c":
                out.append(ch)
            i += 1
            continue
        prev = s[i - 1] if i > 0 else ""
        jp = prev in _F and _F[prev][2] is not None
        nxt = s[i + 1] if i + 1 < n else ""
        if ch == "\u0644" and nxt in _LAM_ALEF:
            out.append(chr(_LAM_ALEF[nxt][1 if jp else 0]))
            i += 2
            continue
        iso, fin, ini, med = _F[ch]
        jn = nxt in _F and ini is not None
        f = med if (jp and jn) else fin if jp else ini if jn else iso
        out.append(chr(f))
        i += 1
    return "".join(out)


def _visual_line(line):
    s = _shape(line)
    if not has_arabic(s):
        return s

    def kind(c):
        if is_arabic(c):
            return "R"
        return "L" if c.isalnum() else "N"

    runs = []
    for c in s:
        k = kind(c)
        if runs and runs[-1][0] == k:
            runs[-1][1] += c
        else:
            runs.append([k, c])
    strong = [r[0] for r in runs if r[0] != "N"]
    base = strong[0] if strong else "L"
    for i, r in enumerate(runs):
        if r[0] != "N":
            continue
        p = next((runs[j][0] for j in range(i - 1, -1, -1) if runs[j][0] != "N"), None)
        q = next((runs[j][0] for j in range(i + 1, len(runs)) if runs[j][0] != "N"), None)
        r[0] = p if (p is not None and p == q) else base
    merged = []
    for k, t in runs:
        if merged and merged[-1][0] == k:
            merged[-1][1] += t
        else:
            merged.append([k, t])
    parts = []
    for k, t in merged:
        if k == "R":
            parts.append("".join(_MIRROR.get(c, c) for c in reversed(t)))
        else:
            parts.append(t)
    if base == "R":
        parts.reverse()
    return "".join(parts)


def bidi(text, lang):
    """Prepare a string for display in a Tk widget."""
    if lang != "fa" or not text or not has_arabic(text):
        return text
    lines = text.split("\n")
    if sys.platform == "win32":
        return "\n".join(("\u202b" + l + "\u202c") if has_arabic(l) else l for l in lines)
    return "\n".join(_visual_line(l) for l in lines)


def tr(lang, key, *args):
    entry = S.get(key)
    s = entry.get(lang, entry["en"]) if entry else key
    if args:
        try:
            s = s % args
        except Exception:
            pass
    return s


def card_text(lang, key):
    en, fa = CARDS[key]
    return fa if lang == "fa" else en
