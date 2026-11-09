# -*- coding: utf-8 -*-
"""HIPERFACE Studio - help content.
Blocks: (kind, text). kind: h1 | p | li | code | cmd | fault | pdf | links"""
from hiperface_i18n import CARDS  # noqa: F401  (cards are rendered by the "cmd" block)

OPCODES = [
    ("tab_pos", [("readpos", "42h"), ("setpos", "43h"), ("setsync", "6Ah"), ("syncoff", "6Ch"),
                 ("analog", "44h"), ("temp", "44h")]),
    ("tab_cnt", [("counter", "46h"), ("inc", "47h"), ("clr", "49h")]),
    ("tab_data", [("rdata", "4Ah"), ("sdata", "4Bh"), ("dstat", "4Ch"), ("mem", "4Eh"), ("create", "4Dh"),
                  ("delete", "4Dh"), ("key", "4Fh")]),
    ("tab_info", [("status", "50h"), ("type", "52h"), ("ext", "4Ah FF"), ("serial", "56h"), ("all", "ALL")]),
    ("tab_cfg", [("reset", "53h"), ("addr", "55h"), ("uart", "BUILD"), ("cfg", "57h"), ("tmp", "67h"),
                 ("adj", "6Bh")]),
    ("tab_raw", [("raw", "RAW")]),
]
CAUTION = {"setpos", "setsync", "clr", "sdata", "create", "delete", "key", "reset", "addr", "cfg", "tmp", "adj"}

EN = [
    ("h1", "Quick start"),
    ("li", "1.  Connect the USB-RS485 adapter to the encoder data lines (A/-, B/+) and power the encoder (7..12 V)."),
    ("li", "2.  Pick the COM port at the top. Press the refresh icon if the adapter was plugged in later."),
    ("li", "3.  Keep the factory settings unless you changed them: 9600 baud, 8E1 (even parity), address 40, Code0 55."),
    ("li", "4.  Press Connect. The green dot means the port is open."),
    ("li", "5.  Open Info & status and press Run on 'Read everything' to check the link in one click."),
    ("p", "No encoder at hand? Choose 'DEMO (simulated)' as the port. The simulator answers like an SRM50: "
          "error frames, access codes, data fields, warning bit, address and UART changes."),

    ("h1", "Toolbar icons"),
    ("li", "?  Help (F1): this window."),
    ("li", "i  About: version, developer, email, repository, specification PDF and system info."),
    ("li", "Globe + EN/FA: language. Persian switches the whole window to right-to-left and uses the Vazirmatn font."),
    ("li", "Sun / moon: dark and light theme. Language, theme and connection settings are saved for the next start."),

    ("h1", "Connection settings"),
    ("li", "Port: the serial port of your USB-RS485 adapter."),
    ("li", "Baud / Parity: must match the encoder. Default is 9600 baud, 8 data bits, even parity, 1 stop bit."),
    ("li", "Addr (hex): encoder address 40..5F (factory 40). FF is the broadcast address: every slave answers "
           "with its own address. Use it only with one encoder on the line."),
    ("li", "Code0 (hex): access code for protected commands (43h, 49h, 55h, 57h, 6Ah, 6Bh). Factory default 55."),
    ("li", "Margin ms: extra wait on top of the spec timing. The app already waits the response time of each "
           "command (Table 10) plus transfer time. Raise it for slow USB adapters."),

    ("h1", "How a frame looks"),
    ("code", "Master:  [Address][Command][Data 0 .. n][Checksum]\n"
             "Slave:   [Address][Command][Data 0 .. m][Checksum]\n"
             "Checksum = XOR of all bytes incl. address.  Example: 40 42 -> 02\n"
             "Error:   [Address][50h][Error code][Checksum]\n"
             "Warning: [Address][Command + 80h][Data ...][Checksum]"),
    ("li", "UART: 1 start, 8 data (LSB first), parity, 1 stop. A frame ends after a pause longer than the timeout "
           "condition (55 / baud = 5.73 ms at 9600). The app keeps this pause between frames."),
    ("li", "Warning bit: when the reply command has bit 7 set, the command worked but the encoder has a stored "
           "warning. The app shows '! warning'. Read it with 50h (Read all codes) to clear the bit."),
    ("li", "Error reply 50h: the command was rejected. D0h means error plus a pending warning."),
    ("li", "After power-on / reset the encoder needs 100..200 ms, uses default settings until ~900 ms and switches "
           "to user settings after 1100 ms. The app waits accordingly after 53h."),

    ("h1", "Live position panel"),
    ("li", "The dial, degrees, raw value and turn count update after every position read."),
    ("li", "Counts / rev: absolute steps per turn = sin/cos periods x 32 (5 bits per period). SRx50: 32768, "
           "SKx36: 4096, SEx34/37/52: 512."),
    ("li", "Live read: reads the position continuously at the chosen interval. Press Stop to end. "
           "Position reads are only reliable below the max speed in the data sheet (typ. 6000 rpm)."),
    ("li", "Snapshot (F5): reads position, status and temperature together."),
    ("li", "Polled frames are not logged by default. Tick 'Log every polled frame' to see them."),

    ("h1", "Commands"),
    ("p", "Each command has its own card. Numbers accept decimal (72), hex with 0x (0x48) or with h (48h). "
          "Fields marked (hex) are read as hex by default."),
    ("cmd", ""),

    ("h1", "Data fields"),
    ("li", "User memory is split into data fields of 16..128 bytes (multiples of 16), numbered 0, 1, 2 ... "
           "Free memory is reported in 16-byte blocks (typ. 1792 bytes = 70h)."),
    ("li", "Each field is linked to Code0..Code3. If 'Code on' is Yes the code must be sent to read or write it. "
           "For creating, the linked code value is always required."),
    ("li", "Status byte: bits 0..2 size (size/16 - 1), bit 3 code on, bits 4..5 code number, bit 6 writable, "
           "bit 7 exists (0 = delete)."),
    ("li", "Only the last field can be enlarged or deleted. Field FF is the read-only extended type label."),

    ("h1", "Caution commands"),
    ("p", "Cards with a red CAUTION badge change data inside the encoder. The app always asks for confirmation first."),
    ("li", "Set encoder address: the reply already comes from the new address; the app follows it."),
    ("li", "Set serial interface (57h) is stored permanently and becomes active after Encoder reset (53h) or a "
           "power cycle. When you reset from the app, the PC port is switched to the new settings automatically."),
    ("li", "Temporarily set serial interface (67h): the reply still uses the old settings, then both sides switch. "
           "A reset brings back the stored settings."),
    ("li", "Set access code: there is no way to restore the default codes. Write the new code down."),
    ("li", "6Ah, 6Bh, 67h, 6Ch are optional commands. Error 0Bh (unknown command) means the encoder does not "
           "support them."),

    ("h1", "Encoder log"),
    ("li", "TX (blue): bytes sent. RX (green): bytes received. The last byte is the XOR checksum."),
    ("li", "✓ decoded result.   ✗ error.   ! warning.   ▸ command started."),
    ("li", "Save writes the log to a .txt file, Copy puts it on the clipboard, Clear empties it (Ctrl+L)."),

    ("h1", "Raw frame"),
    ("p", "Type address + command + data in hex, for example 40 42 for Read position. The XOR checksum is added "
          "for you (preview under the box). Read bytes 0 = read until the frame ends."),

    ("h1", "Fault codes"),
    ("p", "Typical codes from the specification. The codes your encoder really uses are listed in its data sheet."),
    ("fault", ""),

    ("h1", "Troubleshooting"),
    ("li", "No response (timeout): check A/B wiring (try swapping), 130 Ω termination with 1 kΩ bias resistors, "
           "encoder power, address, baud and parity. Raise Margin ms."),
    ("li", "Checksum mismatch: noise or wrong parity. Check grounding, cable shield and parity setting."),
    ("li", "Port busy / Windows error 31: another program holds the port or the adapter driver is stuck. "
           "Close other tools, unplug and replug the adapter, or disable/enable it in Device Manager."),
    ("li", "Error 0Fh wrong access code: Code0 (or the field's access code) does not match the encoder."),
    ("li", "Error 0Bh unknown command: the encoder does not implement that (optional) command."),
    ("li", "Persian text looks plain: put Vazirmatn-Regular.ttf and Vazirmatn-Bold.ttf in the 'fonts' folder "
           "next to the program (get_vazir_font.bat downloads them)."),

    ("h1", "Keyboard shortcuts"),
    ("code", "F1        Help\nF5        Snapshot\nCtrl+L    Clear log\nCtrl+S    Save log\nEsc       Close Help / About"),

    ("h1", "Specification PDF"),
    ("p", "Protocol details follow SICK 'Operating Instructions - Specification HIPERFACE® Motor Feedback Protocol' "
          "(IM0064865). The app looks for the PDF next to the EXE, in the working folder, inside the EXE, and in the "
          "project root below. Click a link to open it."),
    ("pdf", ""),

    ("h1", "Contact"),
    ("links", ""),
]

FA = [
    ("h1", "شروع سریع"),
    ("li", "1.  مبدل USB-RS485 را به خطوط داده‌ی انکودر (A/- و B/+) وصل کنید و انکودر را روشن کنید (7 تا 12 ولت)."),
    ("li", "2.  پورت COM را از بالای صفحه انتخاب کنید. اگر مبدل را بعداً وصل کردید، آیکون به‌روزرسانی را بزنید."),
    ("li", "3.  اگر تنظیمات انکودر را تغییر نداده‌اید پیش‌فرض‌ها را نگه دارید: 9600 باود، 8E1 (پریتی زوج)، آدرس 40، Code0 برابر 55."),
    ("li", "4.  دکمه‌ی «اتصال» را بزنید. نقطه‌ی سبز یعنی پورت باز است."),
    ("li", "5.  در تب «اطلاعات و وضعیت» روی «خواندن همه» بزنید تا ارتباط با یک کلیک بررسی شود."),
    ("p", "انکودر در دسترس ندارید؟ پورت «DEMO (simulated)» را انتخاب کنید. شبیه‌ساز مثل SRM50 پاسخ می‌دهد: "
          "فریم خطا، کد دسترسی، فیلد داده، بیت هشدار و تغییر آدرس و تنظیمات UART."),

    ("h1", "آیکون‌های نوار بالا"),
    ("li", "?  راهنما (F1): همین پنجره."),
    ("li", "i  درباره: نسخه، توسعه‌دهنده، ایمیل، ریپازیتوری، PDF مستند و اطلاعات سیستم."),
    ("li", "کره + EN/FA: انتخاب زبان. فارسی کل پنجره را راست‌به‌چپ می‌کند و از فونت وزیر (Vazirmatn) استفاده می‌کند."),
    ("li", "خورشید / ماه: تم تیره و روشن. زبان، تم و تنظیمات اتصال برای اجرای بعدی ذخیره می‌شوند."),

    ("h1", "تنظیمات اتصال"),
    ("li", "پورت: پورت سریال مبدل USB-RS485."),
    ("li", "باود و پریتی: باید با انکودر یکی باشد. پیش‌فرض 9600 باود، 8 بیت داده، پریتی زوج و 1 بیت توقف است."),
    ("li", "آدرس (hex): آدرس انکودر بین 40 تا 5F (پیش‌فرض 40). FF آدرس همگانی است و هر اسلیو با آدرس خودش پاسخ می‌دهد؛ "
           "فقط وقتی یک انکودر روی خط است از آن استفاده کنید."),
    ("li", "Code0 (hex): کد دسترسی دستورهای حفاظت‌شده (43h، 49h، 55h، 57h، 6Ah، 6Bh). پیش‌فرض 55."),
    ("li", "حاشیه ms: زمان انتظار اضافه روی زمان‌بندی مستند. برنامه خودش زمان پاسخ هر دستور (جدول 10) و زمان انتقال را "
           "صبر می‌کند. برای مبدل‌های USB کند آن را بیشتر کنید."),

    ("h1", "ساختار فریم"),
    ("code", "Master:  [Address][Command][Data 0 .. n][Checksum]\n"
             "Slave:   [Address][Command][Data 0 .. m][Checksum]\n"
             "Checksum = XOR of all bytes incl. address.  Example: 40 42 -> 02\n"
             "Error:   [Address][50h][Error code][Checksum]\n"
             "Warning: [Address][Command + 80h][Data ...][Checksum]"),
    ("li", "UART: یک بیت شروع، 8 بیت داده (LSB اول)، پریتی و یک بیت توقف. پایان فریم با سکوتی بیشتر از تایم‌اوت "
           "(55 تقسیم بر باود = 5.73 میلی‌ثانیه در 9600) مشخص می‌شود و برنامه این فاصله را رعایت می‌کند."),
    ("li", "بیت هشدار: اگر بیت 7 دستور در پاسخ فعال باشد، دستور درست اجرا شده ولی انکودر هشدار ذخیره‌شده دارد. "
           "برنامه «! هشدار» نشان می‌دهد. با 50h (خواندن همه‌ی کدها) آن را بخوانید تا بیت پاک شود."),
    ("li", "پاسخ خطای 50h یعنی دستور رد شده است. D0h یعنی خطا به‌همراه هشدار معلق."),
    ("li", "بعد از روشن شدن یا ریست، انکودر 100 تا 200 میلی‌ثانیه راه‌اندازی می‌شود، تا حدود 900 میلی‌ثانیه با تنظیمات "
           "پیش‌فرض کار می‌کند و بعد از 1100 میلی‌ثانیه به تنظیمات کاربر می‌رود. برنامه بعد از 53h همین قدر صبر می‌کند."),

    ("h1", "پنل موقعیت زنده"),
    ("li", "عقربه، درجه، مقدار خام و تعداد دور بعد از هر بار خواندن موقعیت به‌روز می‌شوند."),
    ("li", "پالس در دور: تعداد گام مطلق در هر دور = تعداد پریود سینوس/کسینوس × 32 (5 بیت در هر پریود). "
           "SRx50: عدد 32768، SKx36: عدد 4096، SEx34/37/52: عدد 512."),
    ("li", "خواندن زنده: موقعیت را با فاصله‌ی انتخاب‌شده پشت سر هم می‌خواند. خواندن موقعیت فقط زیر حداکثر سرعت دیتاشیت "
           "(معمولاً 6000 دور در دقیقه) معتبر است."),
    ("li", "اسنپ‌شات (F5): موقعیت، وضعیت و دما را با هم می‌خواند."),
    ("li", "فریم‌های خواندن زنده به‌طور پیش‌فرض در لاگ ثبت نمی‌شوند. برای دیدن آن‌ها تیک گزینه‌ی مربوط را بزنید."),

    ("h1", "دستورها"),
    ("p", "هر دستور کارت مخصوص خودش را دارد. اعداد به‌صورت دهدهی (72)، هگز با 0x (0x48) یا با h (48h) پذیرفته می‌شوند. "
          "فیلدهایی که (hex) دارند به‌طور پیش‌فرض هگز خوانده می‌شوند."),
    ("cmd", ""),

    ("h1", "فیلدهای داده"),
    ("li", "حافظه‌ی کاربر به فیلدهای 16 تا 128 بایتی (مضرب 16) با شماره‌های 0، 1، 2 ... تقسیم می‌شود. "
           "حافظه‌ی آزاد بر حسب بلوک 16 بایتی گزارش می‌شود (معمولاً 1792 بایت = 70h)."),
    ("li", "هر فیلد به یکی از کدهای Code0 تا Code3 وصل است. اگر «کد فعال» بله باشد، برای خواندن و نوشتن باید کد ارسال شود. "
           "برای ایجاد فیلد، مقدار کد مربوط همیشه لازم است."),
    ("li", "بایت وضعیت: بیت 0 تا 2 اندازه (اندازه/16 منهای 1)، بیت 3 فعال بودن کد، بیت 4 و 5 شماره‌ی کد، بیت 6 قابل نوشتن، "
           "بیت 7 وجود فیلد (0 = حذف)."),
    ("li", "فقط آخرین فیلد قابل بزرگ کردن یا حذف است. فیلد FF برچسب نوع توسعه‌یافته و فقط‌خواندنی است."),

    ("h1", "دستورهای حساس"),
    ("p", "کارت‌هایی که برچسب قرمز «احتیاط» دارند داده‌ی داخل انکودر را تغییر می‌دهند و برنامه همیشه قبل از اجرا تأیید می‌گیرد."),
    ("li", "تغییر آدرس انکودر: پاسخ از آدرس جدید می‌آید و برنامه خودکار به آن سوئیچ می‌کند."),
    ("li", "تنظیم رابط سریال (57h) دائمی ذخیره می‌شود و بعد از ریست انکودر (53h) یا قطع و وصل برق فعال می‌شود. "
           "اگر ریست را از داخل برنامه بزنید، پورت کامپیوتر هم خودکار به تنظیمات جدید می‌رود."),
    ("li", "تنظیم موقت رابط سریال (67h): پاسخ هنوز با تنظیمات قبلی می‌آید و بعد هر دو طرف تغییر می‌کنند. با ریست، "
           "تنظیمات ذخیره‌شده برمی‌گردد."),
    ("li", "تغییر کد دسترسی: راهی برای برگرداندن کدها به پیش‌فرض وجود ندارد. کد جدید را یادداشت کنید."),
    ("li", "دستورهای 6Ah، 6Bh، 67h و 6Ch اختیاری‌اند. خطای 0Bh (دستور ناشناخته) یعنی انکودر از آن پشتیبانی نمی‌کند."),

    ("h1", "لاگ انکودر"),
    ("li", "TX (آبی): بایت‌های ارسالی. RX (سبز): بایت‌های دریافتی. آخرین بایت چک‌سام XOR است."),
    ("li", "✓ نتیجه‌ی تفسیرشده.   ✗ خطا.   ! هشدار.   ▸ شروع دستور."),
    ("li", "«ذخیره» لاگ را در فایل txt ذخیره می‌کند، «کپی» آن را در کلیپ‌بورد می‌گذارد و «پاک کردن» آن را خالی می‌کند (Ctrl+L)."),

    ("h1", "فریم خام"),
    ("p", "آدرس، دستور و داده را به‌صورت هگز وارد کنید، مثلاً 40 42 برای خواندن موقعیت. چک‌سام XOR خودکار اضافه می‌شود "
          "و پیش‌نمایش آن زیر کادر دیده می‌شود. بایت دریافتی 0 یعنی تا پایان فریم خوانده شود."),

    ("h1", "کدهای خطا"),
    ("p", "کدهای رایج مستند. کدهایی که انکودر شما واقعاً استفاده می‌کند در دیتاشیت آن آمده است."),
    ("fault", ""),

    ("h1", "رفع اشکال"),
    ("li", "پاسخی دریافت نشد (timeout): سیم‌کشی A و B (جابه‌جا هم امتحان کنید)، ترمینیشن 130 اهم با مقاومت‌های بایاس "
           "1 کیلواهم، تغذیه‌ی انکودر، آدرس، باود و پریتی را بررسی کنید و «حاشیه ms» را بیشتر کنید."),
    ("li", "خطای چک‌سام: نویز یا پریتی اشتباه. اتصال زمین، شیلد کابل و تنظیم پریتی را بررسی کنید."),
    ("li", "پورت مشغول یا خطای 31 ویندوز: برنامه‌ی دیگری پورت را گرفته یا درایور مبدل گیر کرده. برنامه‌های دیگر را ببندید، "
           "مبدل را جدا و وصل کنید یا در Device Manager غیرفعال و دوباره فعال کنید."),
    ("li", "خطای 0Fh کد دسترسی نادرست: Code0 یا کد دسترسی فیلد با انکودر یکی نیست."),
    ("li", "خطای 0Bh دستور ناشناخته: انکودر آن دستور (اختیاری) را پیاده‌سازی نکرده است."),
    ("li", "متن فارسی با فونت وزیر نمایش داده نمی‌شود: فایل‌های Vazirmatn-Regular.ttf و Vazirmatn-Bold.ttf را در پوشه‌ی "
           "fonts کنار برنامه قرار دهید (فایل get_vazir_font.bat آن‌ها را دانلود می‌کند)."),

    ("h1", "میانبرهای صفحه‌کلید"),
    ("code", "F1        Help\nF5        Snapshot\nCtrl+L    Clear log\nCtrl+S    Save log\nEsc       Close Help / About"),

    ("h1", "فایل PDF مستند"),
    ("p", "جزئیات پروتکل بر اساس مستند SICK با عنوان Operating Instructions - Specification HIPERFACE® Motor Feedback "
          "Protocol (IM0064865) است. برنامه PDF را کنار EXE، در پوشه‌ی جاری، داخل EXE و در ریشه‌ی پروژه (مسیر زیر) "
          "جستجو می‌کند. برای باز کردن روی لینک بزنید."),
    ("pdf", ""),

    ("h1", "ارتباط با توسعه‌دهنده"),
    ("links", ""),
]


def blocks(lang):
    return FA if lang == "fa" else EN
