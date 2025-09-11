package com.example.smsreceiverapp

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.telephony.SmsMessage
import android.util.Log
import android.widget.Toast
import com.example.smsreceiverapp.MainActivity.Companion.lastSmsCallback
import com.example.smsreceiverapp.MainActivity.Companion.lastSender
import com.example.smsreceiverapp.MainActivity.Companion.lastMessage
import com.example.smsreceiverapp.MainActivity.Companion.lastLat
import com.example.smsreceiverapp.MainActivity.Companion.lastLon

class SmsReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == "android.provider.Telephony.SMS_RECEIVED") {
            val bundle = intent.extras
            try {
                val pdus = bundle?.get("pdus") as Array<*>
                for (pdu in pdus) {
                    val format = bundle.getString("format")
                    val sms = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                        SmsMessage.createFromPdu(pdu as ByteArray, format)
                    } else {
                        SmsMessage.createFromPdu(pdu as ByteArray)
                    }

                    val sender = sms.originatingAddress ?: "Unknown"
                    val message = sms.messageBody ?: ""

                    // ✅ Show Toast
                    Toast.makeText(context, "SMS from $sender: $message", Toast.LENGTH_LONG).show()

                    // ✅ Update stored values for MainActivity
                    val formattedMsg = "From: $sender\n$message"
                    lastSender = sender
                    lastMessage = message

                    val parts = message.split(",")
                    if (parts.size == 2) {
                        lastLat = parts[0].trim()
                        lastLon = parts[1].trim()
                    } else {
                        lastLat = null
                        lastLon = null
                        Log.e("SmsReceiver", "❌ Invalid SMS format: $message")
                    }

                    // ✅ Update UI if app is open
                    lastSmsCallback?.invoke(formattedMsg)
                }
            } catch (e: Exception) {
                Log.e("SmsReceiver", "Error receiving SMS", e)
            }
        }
    }
}
