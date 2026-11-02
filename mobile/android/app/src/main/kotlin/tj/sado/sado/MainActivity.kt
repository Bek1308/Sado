package tj.sado.sado

import android.content.Intent
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val phone by lazy { PhoneControl(this) }

    /** Set when Sado was opened to talk: from the assist button, the tile or a shortcut. */
    private var talkRequested = false

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, PhoneControl.CHANNEL)
            .setMethodCallHandler(phone)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, LAUNCH_CHANNEL)
            .setMethodCallHandler { call, result ->
                if (call.method == "takeTalkRequest") {
                    result.success(talkRequested)
                    talkRequested = false
                } else {
                    result.notImplemented()
                }
            }
        notice(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        notice(intent)
    }

    private fun notice(intent: Intent?) {
        talkRequested = talkRequested || intent?.action in TALK_ACTIONS
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray,
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PhoneControl.PERMISSION_REQUEST) phone.onPermissionResult()
    }

    companion object {
        const val ACTION_TALK = "tj.sado.sado.TALK"
        private const val LAUNCH_CHANNEL = "sado/launch"
        private val TALK_ACTIONS = setOf(
            ACTION_TALK,
            Intent.ACTION_ASSIST,
            Intent.ACTION_VOICE_COMMAND,
        )
    }
}
