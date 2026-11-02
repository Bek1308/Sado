package tj.sado.sado

import android.Manifest
import android.app.Activity
import android.app.SearchManager
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.hardware.camera2.CameraAccessException
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraManager
import android.media.AudioManager
import android.net.Uri
import android.os.BatteryManager
import android.provider.AlarmClock
import android.provider.CalendarContract
import android.provider.ContactsContract
import android.provider.MediaStore
import android.provider.Settings
import android.telephony.SmsManager
import android.view.KeyEvent
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import java.time.OffsetDateTime

/**
 * Carries out what Sado asked the phone to do. Most actions happen at once: alarms, timers,
 * music, volume, the flashlight. Calls and text messages are placed and sent by the phone
 * itself, but the Flutter side only asks for them after the user said yes.
 *
 * Contacts are looked up here and never leave the phone.
 */
class PhoneControl(private val activity: Activity) : MethodChannel.MethodCallHandler {
    private var waitingForPermission: (() -> Unit)? = null

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "perform" -> {
                val kind = call.argument<String>("kind").orEmpty()
                val details = call.argument<Map<String, String>>("details").orEmpty()
                perform(kind, details) { outcome -> result.success(outcome) }
            }
            "status" -> result.success(status())
            else -> result.notImplemented()
        }
    }

    /** Called from the activity once the user answered a permission request. */
    fun onPermissionResult() {
        waitingForPermission?.invoke()
        waitingForPermission = null
    }

    private fun perform(kind: String, details: Map<String, String>, done: (String) -> Unit) {
        try {
            when (kind) {
                "call" -> call(details["contact"].orEmpty(), done)
                "message" -> message(details, done)
                "alarm" -> done(alarm(details))
                "timer" -> done(timer(details))
                "open" -> done(open(details["target"].orEmpty()))
                "navigate" -> done(view("geo:0,0?q=" + Uri.encode(details["destination"].orEmpty())))
                "flashlight" -> done(flashlight(details["on"] == "true"))
                "volume" -> done(volume(details["change"].orEmpty()))
                "media" -> done(media(details["key"].orEmpty()))
                "play" -> done(play(details["query"].orEmpty()))
                "calendar" -> done(calendar(details))
                "email" -> done(email(details))
                "settings" -> done(settings(details["page"].orEmpty()))
                "search" -> done(search(details["query"].orEmpty()))
                else -> done(FAILED)
            }
        } catch (error: SecurityException) {
            done(FAILED)
        }
    }

    /** Places the call; without the permission, the dialer opens with the number ready. */
    private fun call(contact: String, done: (String) -> Unit) =
        withNumber(contact, done) { number ->
            val tel = Uri.parse("tel:" + Uri.encode(number))
            withPermission(Manifest.permission.CALL_PHONE, done, orElse = {
                start(Intent(Intent.ACTION_DIAL, tel))
            }) { start(Intent(Intent.ACTION_CALL, tel)) }
        }

    private fun message(details: Map<String, String>, done: (String) -> Unit) {
        val text = details["text"].orEmpty()
        when (details["app"]) {
            // Telegram cannot open a chat by phone number, so the user picks the chat.
            "telegram" -> done(
                start(
                    Intent(Intent.ACTION_SEND)
                        .setType("text/plain")
                        .putExtra(Intent.EXTRA_TEXT, text)
                        .setPackage("org.telegram.messenger"),
                ),
            )
            "whatsapp" -> withNumber(details["contact"].orEmpty(), done) { number ->
                val digits = number.filter { it.isDigit() }
                done(
                    start(
                        Intent(
                            Intent.ACTION_VIEW,
                            Uri.parse("https://wa.me/$digits?text=" + Uri.encode(text)),
                        ).setPackage("com.whatsapp"),
                    ),
                )
            }
            else -> withNumber(details["contact"].orEmpty(), done) { number ->
                withPermission(Manifest.permission.SEND_SMS, done, orElse = {
                    start(
                        Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:" + Uri.encode(number)))
                            .putExtra("sms_body", text),
                    )
                }) { sendSms(number, text) }
            }
        }
    }

    @Suppress("DEPRECATION")
    private fun sendSms(number: String, text: String): String {
        val sms = activity.getSystemService(SmsManager::class.java) ?: SmsManager.getDefault()
        val parts = sms.divideMessage(text)
        sms.sendMultipartTextMessage(number, null, parts, null, null)
        return DONE
    }

    private fun alarm(details: Map<String, String>): String {
        val intent = Intent(AlarmClock.ACTION_SET_ALARM)
            .putExtra(AlarmClock.EXTRA_HOUR, details["hour"]?.toIntOrNull() ?: return FAILED)
            .putExtra(AlarmClock.EXTRA_MINUTES, details["minute"]?.toIntOrNull() ?: return FAILED)
            .putExtra(AlarmClock.EXTRA_SKIP_UI, true)
        details["label"]?.takeIf { it.isNotBlank() }?.let {
            intent.putExtra(AlarmClock.EXTRA_MESSAGE, it)
        }
        return start(intent)
    }

    private fun timer(details: Map<String, String>): String {
        val intent = Intent(AlarmClock.ACTION_SET_TIMER)
            .putExtra(AlarmClock.EXTRA_LENGTH, details["seconds"]?.toIntOrNull() ?: return FAILED)
            .putExtra(AlarmClock.EXTRA_SKIP_UI, true)
        details["label"]?.takeIf { it.isNotBlank() }?.let {
            intent.putExtra(AlarmClock.EXTRA_MESSAGE, it)
        }
        return start(intent)
    }

    private fun open(target: String): String {
        val name = target.trim()
        if (WEB_ADDRESS.matches(name)) {
            return view(if (name.contains("://")) name else "https://$name")
        }
        when (simplify(name)) {
            "camera", "kamera", "камера" ->
                return start(Intent(MediaStore.INTENT_ACTION_STILL_IMAGE_CAMERA))
            "settings", "sozlamalar", "настройки" ->
                return start(Intent(Settings.ACTION_SETTINGS))
        }
        val launcher = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        val apps = activity.packageManager.queryIntentActivities(launcher, 0)
        val app = best(apps, name) { app ->
            listOf(app.loadLabel(activity.packageManager).toString(), app.activityInfo.packageName)
        } ?: return APP_NOT_FOUND
        val intent = activity.packageManager.getLaunchIntentForPackage(app.activityInfo.packageName)
            ?: return APP_NOT_FOUND
        return start(intent)
    }

    private fun flashlight(on: Boolean): String {
        val cameras = activity.getSystemService(Context.CAMERA_SERVICE) as CameraManager
        return try {
            val camera = cameras.cameraIdList.firstOrNull {
                cameras.getCameraCharacteristics(it)
                    .get(CameraCharacteristics.FLASH_INFO_AVAILABLE) == true
            } ?: return FAILED
            cameras.setTorchMode(camera, on)
            DONE
        } catch (error: CameraAccessException) {
            FAILED
        }
    }

    private fun volume(change: String): String {
        val audio = activity.getSystemService(Context.AUDIO_SERVICE) as AudioManager
        val stream = AudioManager.STREAM_MUSIC
        val shown = AudioManager.FLAG_SHOW_UI
        when (change) {
            // A few steps at once, so "louder" is clearly louder.
            "up" -> repeat(VOLUME_STEPS) {
                audio.adjustStreamVolume(stream, AudioManager.ADJUST_RAISE, shown)
            }
            "down" -> repeat(VOLUME_STEPS) {
                audio.adjustStreamVolume(stream, AudioManager.ADJUST_LOWER, shown)
            }
            "mute" -> audio.adjustStreamVolume(stream, AudioManager.ADJUST_MUTE, shown)
            "unmute" -> audio.adjustStreamVolume(stream, AudioManager.ADJUST_UNMUTE, shown)
            "max" -> audio.setStreamVolume(stream, audio.getStreamMaxVolume(stream), shown)
            else -> return FAILED
        }
        return DONE
    }

    private fun media(key: String): String {
        val code = when (key) {
            "play_pause" -> KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE
            "next" -> KeyEvent.KEYCODE_MEDIA_NEXT
            "previous" -> KeyEvent.KEYCODE_MEDIA_PREVIOUS
            else -> return FAILED
        }
        val audio = activity.getSystemService(Context.AUDIO_SERVICE) as AudioManager
        audio.dispatchMediaKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, code))
        audio.dispatchMediaKeyEvent(KeyEvent(KeyEvent.ACTION_UP, code))
        return DONE
    }

    /** Music apps such as YouTube Music start playing straight from a search. */
    private fun play(query: String): String {
        val played = start(
            Intent(MediaStore.INTENT_ACTION_MEDIA_PLAY_FROM_SEARCH)
                .putExtra(SearchManager.QUERY, query)
                .putExtra(MediaStore.EXTRA_MEDIA_FOCUS, "vnd.android.cursor.item/*"),
        )
        if (played == DONE) return DONE
        return view("https://www.youtube.com/results?search_query=" + Uri.encode(query))
    }

    private fun calendar(details: Map<String, String>): String {
        val start = runCatching { OffsetDateTime.parse(details["start"]) }.getOrNull()
            ?: return FAILED
        val begin = start.toInstant().toEpochMilli()
        val minutes = details["minutes"]?.toLongOrNull() ?: DEFAULT_EVENT_MINUTES
        return start(
            Intent(Intent.ACTION_INSERT, CalendarContract.Events.CONTENT_URI)
                .putExtra(CalendarContract.Events.TITLE, details["title"].orEmpty())
                .putExtra(CalendarContract.EXTRA_EVENT_BEGIN_TIME, begin)
                .putExtra(CalendarContract.EXTRA_EVENT_END_TIME, begin + minutes * 60_000),
        )
    }

    private fun email(details: Map<String, String>): String = start(
        Intent(Intent.ACTION_SENDTO, Uri.parse("mailto:"))
            .putExtra(Intent.EXTRA_EMAIL, arrayOf(details["to"].orEmpty()))
            .putExtra(Intent.EXTRA_SUBJECT, details["subject"].orEmpty())
            .putExtra(Intent.EXTRA_TEXT, details["body"].orEmpty()),
    )

    private fun settings(page: String): String {
        val action = when (page) {
            "wifi" -> Settings.ACTION_WIFI_SETTINGS
            "bluetooth" -> Settings.ACTION_BLUETOOTH_SETTINGS
            "display" -> Settings.ACTION_DISPLAY_SETTINGS
            "sound" -> Settings.ACTION_SOUND_SETTINGS
            "battery" -> Intent.ACTION_POWER_USAGE_SUMMARY
            "location" -> Settings.ACTION_LOCATION_SOURCE_SETTINGS
            "airplane" -> Settings.ACTION_AIRPLANE_MODE_SETTINGS
            else -> Settings.ACTION_SETTINGS
        }
        return start(Intent(action))
    }

    private fun search(query: String): String {
        val searched = start(Intent(Intent.ACTION_WEB_SEARCH).putExtra(SearchManager.QUERY, query))
        if (searched == DONE) return DONE
        return view("https://www.google.com/search?q=" + Uri.encode(query))
    }

    /** What the phone tells Sado about itself with every question, e.g. its battery. */
    private fun status(): String {
        val battery = activity.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        val level = battery.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        val charging = if (battery.isCharging) "charging" else "not charging"
        val audio = activity.getSystemService(Context.AUDIO_SERVICE) as AudioManager
        val stream = AudioManager.STREAM_MUSIC
        val volume = audio.getStreamVolume(stream) * 100 / audio.getStreamMaxVolume(stream)
        return "Battery $level%, $charging. Media volume $volume%."
    }

    /** Finds the phone number for `contact`, asking for the contacts permission once. */
    private fun withNumber(contact: String, done: (String) -> Unit, use: (String) -> Unit) {
        if (PHONE_NUMBER.matches(contact)) return use(contact)
        withPermission(Manifest.permission.READ_CONTACTS, done, orElse = { NO_PERMISSION }) {
            val number = lookUp(contact)
            if (number == null) CONTACT_NOT_FOUND else {
                use(number)
                PENDING
            }
        }
    }

    /**
     * Runs `granted` once the user allowed `permission`, asking them if needed, and
     * `orElse` when they refuse. Whatever either returns goes to `done`, unless it is
     * PENDING: then the work reports through `done` itself.
     */
    private fun withPermission(
        permission: String,
        done: (String) -> Unit,
        orElse: () -> String,
        granted: () -> String,
    ) {
        fun finish(outcome: String) {
            if (outcome != PENDING) done(outcome)
        }
        if (activity.checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED) {
            return finish(granted())
        }
        waitingForPermission = {
            val allowed = activity.checkSelfPermission(permission) ==
                PackageManager.PERMISSION_GRANTED
            finish(if (allowed) granted() else orElse())
        }
        activity.requestPermissions(arrayOf(permission), PERMISSION_REQUEST)
    }

    private fun lookUp(contact: String): String? {
        val people = mutableListOf<Pair<String, String>>()
        activity.contentResolver.query(
            ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
            arrayOf(
                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                ContactsContract.CommonDataKinds.Phone.NUMBER,
            ),
            null,
            null,
            null,
        )?.use { rows ->
            while (rows.moveToNext()) {
                val name = rows.getString(0) ?: continue
                val number = rows.getString(1) ?: continue
                people += name to number
            }
        }
        return best(people, contact) { listOf(it.first) }?.second
    }

    private fun view(address: String): String =
        start(Intent(Intent.ACTION_VIEW, Uri.parse(address)))

    private fun start(intent: Intent): String = try {
        activity.startActivity(intent)
        DONE
    } catch (error: ActivityNotFoundException) {
        APP_NOT_FOUND
    }

    companion object {
        const val CHANNEL = "sado/phone"
        const val PERMISSION_REQUEST = 4107

        private const val DONE = "done"
        private const val PENDING = "pending"
        private const val CONTACT_NOT_FOUND = "contact_not_found"
        private const val APP_NOT_FOUND = "app_not_found"
        private const val NO_PERMISSION = "no_permission"
        private const val FAILED = "failed"
        private const val VOLUME_STEPS = 3
        private const val DEFAULT_EVENT_MINUTES = 60L

        private val PHONE_NUMBER = Regex("""^\+?[\d\s()-]{3,}$""")
        private val WEB_ADDRESS = Regex("""^(https?://)?[\w-]+(\.[\w-]+)+(/\S*)?$""")

        /**
         * The closest match for what the user said: an exact name first, then a name that
         * starts with it, then one that contains it. Latin and Cyrillic spellings meet in
         * the middle, so "Onam" finds "Онам".
         */
        fun <T> best(candidates: List<T>, wanted: String, names: (T) -> List<String>): T? {
            val target = simplify(wanted)
            if (target.isEmpty()) return null
            return candidates
                .map { candidate -> candidate to names(candidate).maxOf { score(simplify(it), target) } }
                .filter { it.second > 0 }
                .maxByOrNull { it.second }
                ?.first
        }

        private fun score(name: String, target: String): Int = when {
            name == target -> 3
            name.split(' ').any { it.startsWith(target) } -> 2
            name.contains(target) || (target.length >= 4 && target.contains(name)) -> 1
            else -> 0
        }

        fun simplify(text: String): String = text.lowercase()
            .map { LATIN[it] ?: it.toString() }
            .joinToString("")
            .filter { it.isLetterOrDigit() || it == ' ' || it == '.' }
            .trim()

        private val LATIN = mapOf(
            'а' to "a", 'б' to "b", 'в' to "v", 'г' to "g", 'ғ' to "g", 'д' to "d",
            'е' to "e", 'ё' to "yo", 'ж' to "j", 'з' to "z", 'и' to "i", 'ӣ' to "i",
            'й' to "y", 'к' to "k", 'қ' to "q", 'л' to "l", 'м' to "m", 'н' to "n",
            'о' to "o", 'п' to "p", 'р' to "r", 'с' to "s", 'т' to "t", 'у' to "u",
            'ӯ' to "u", 'ў' to "o", 'ф' to "f", 'х' to "x", 'ҳ' to "h", 'ц' to "ts",
            'ч' to "ch", 'ҷ' to "j", 'ш' to "sh", 'щ' to "sh", 'ъ' to "", 'ы' to "i",
            'ь' to "", 'э' to "e", 'ю' to "yu", 'я' to "ya",
            // Uzbek Latin writes o' and g' with any of these apostrophes.
            '\'' to "", '’' to "", 'ʻ' to "", 'ʼ' to "", '`' to "",
        )
    }
}
