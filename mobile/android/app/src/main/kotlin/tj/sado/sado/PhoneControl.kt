package tj.sado.sado

import android.Manifest
import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.hardware.camera2.CameraAccessException
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraManager
import android.net.Uri
import android.provider.AlarmClock
import android.provider.ContactsContract
import android.provider.MediaStore
import android.provider.Settings
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel

/**
 * Carries out what Sado asked the phone to do, with the phone's own screens: the dialer,
 * the message composer, the clock, maps. Calls and messages still wait for the user's tap.
 *
 * Contacts are looked up here and never leave the phone.
 */
class PhoneControl(private val activity: Activity) : MethodChannel.MethodCallHandler {
    private var waitingForContacts: (() -> Unit)? = null

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        if (call.method != "perform") return result.notImplemented()
        val kind = call.argument<String>("kind").orEmpty()
        val details = call.argument<Map<String, String>>("details").orEmpty()
        perform(kind, details) { outcome -> result.success(outcome) }
    }

    /** Called from the activity once the user answered the contacts permission. */
    fun onContactsPermission() {
        waitingForContacts?.invoke()
        waitingForContacts = null
    }

    private fun perform(kind: String, details: Map<String, String>, done: (String) -> Unit) {
        try {
            when (kind) {
                "call" -> withNumber(details["contact"].orEmpty(), done) { number ->
                    start(Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + Uri.encode(number))))
                }
                "message" -> message(details, done)
                "alarm" -> done(alarm(details))
                "timer" -> done(timer(details))
                "open" -> done(open(details["target"].orEmpty()))
                "navigate" -> done(
                    start(
                        Intent(
                            Intent.ACTION_VIEW,
                            Uri.parse("geo:0,0?q=" + Uri.encode(details["destination"].orEmpty())),
                        ),
                    ),
                )
                "flashlight" -> done(flashlight(details["on"] == "true"))
                else -> done(FAILED)
            }
        } catch (error: SecurityException) {
            done(FAILED)
        }
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
                start(
                    Intent(
                        Intent.ACTION_VIEW,
                        Uri.parse("https://wa.me/$digits?text=" + Uri.encode(text)),
                    ).setPackage("com.whatsapp"),
                )
            }
            else -> withNumber(details["contact"].orEmpty(), done) { number ->
                start(
                    Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:" + Uri.encode(number)))
                        .putExtra("sms_body", text),
                )
            }
        }
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
            val address = if (name.contains("://")) name else "https://$name"
            return start(Intent(Intent.ACTION_VIEW, Uri.parse(address)))
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

    /** Finds the phone number for `contact`, asking for the contacts permission once. */
    private fun withNumber(contact: String, done: (String) -> Unit, use: (String) -> String) {
        if (PHONE_NUMBER.matches(contact)) return done(use(contact))
        val granted = activity.checkSelfPermission(Manifest.permission.READ_CONTACTS) ==
            PackageManager.PERMISSION_GRANTED
        if (granted) return done(lookUp(contact)?.let(use) ?: CONTACT_NOT_FOUND)
        waitingForContacts = {
            val nowGranted = activity.checkSelfPermission(Manifest.permission.READ_CONTACTS) ==
                PackageManager.PERMISSION_GRANTED
            done(if (nowGranted) lookUp(contact)?.let(use) ?: CONTACT_NOT_FOUND else NO_PERMISSION)
        }
        activity.requestPermissions(arrayOf(Manifest.permission.READ_CONTACTS), CONTACTS_REQUEST)
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

    private fun start(intent: Intent): String = try {
        activity.startActivity(intent)
        DONE
    } catch (error: ActivityNotFoundException) {
        APP_NOT_FOUND
    }

    companion object {
        const val CHANNEL = "sado/phone"
        const val CONTACTS_REQUEST = 4107

        private const val DONE = "done"
        private const val CONTACT_NOT_FOUND = "contact_not_found"
        private const val APP_NOT_FOUND = "app_not_found"
        private const val NO_PERMISSION = "no_permission"
        private const val FAILED = "failed"

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
