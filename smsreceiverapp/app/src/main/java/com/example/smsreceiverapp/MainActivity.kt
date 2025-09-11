package com.example.smsreceiverapp

import android.Manifest
import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException

class MainActivity : ComponentActivity() {

    private lateinit var lastSmsText: TextView
    private lateinit var locationText: TextView
    private lateinit var updateBtn: Button
    private lateinit var forwardBtn: Button

    companion object {
        // Stores latest SMS info
        var lastSender: String? = null
        var lastMessage: String? = null
        var lastLat: String? = null
        var lastLon: String? = null

        // Callback to update UI
        var lastSmsCallback: ((String) -> Unit)? = null
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        lastSmsText = findViewById(R.id.lastSms)
        locationText = findViewById(R.id.locationText)
        updateBtn = findViewById(R.id.updateLocationBtn)
        forwardBtn = findViewById(R.id.forwardBtn)

        // Request SMS permission
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECEIVE_SMS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.RECEIVE_SMS, Manifest.permission.READ_SMS),
                1
            )
        }

        // When new SMS arrives, update UI
        lastSmsCallback = { sms ->
            runOnUiThread {
                lastSmsText.text = sms

                // Try parsing coordinates
                val parts = sms.substringAfter("\n").split(",")
                if (parts.size == 2) {
                    lastLat = parts[0].trim()
                    lastLon = parts[1].trim()
                    locationText.text = "Lat: $lastLat, Lon: $lastLon"
                } else {
                    locationText.text = "Invalid SMS format"
                }
            }
        }

        updateBtn.setOnClickListener {
            Toast.makeText(this, "Waiting for new SMS...", Toast.LENGTH_SHORT).show()
        }

        // ✅ Forward to server manually
        forwardBtn.setOnClickListener {
            if (lastLat != null && lastLon != null) {
                forwardToServer(lastSender, lastMessage, lastLat!!, lastLon!!)
            } else {
                Toast.makeText(this, "No location data to forward", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun forwardToServer(sender: String?, message: String?, lat: String, lon: String) {
        val client = OkHttpClient()
        val json = JSONObject().apply {
            put("sender", sender ?: "unknown")
            put("message", message ?: "")
            put("latitude", lat)
            put("longitude", lon)
        }

        val body = json.toString().toRequestBody("application/json".toMediaType())
        val request = Request.Builder()
            .url(" https://92473fdc5dac.ngrok-free.app/receive_sms") // change to your Flask server
            .post(body)
            .build()

        Thread {
            try {
                val response = client.newCall(request).execute()
                val respBody = response.body?.string()
                runOnUiThread {
                    Toast.makeText(this, "📤 Sent: $respBody", Toast.LENGTH_LONG).show()
                }
            } catch (e: IOException) {
                runOnUiThread {
                    Toast.makeText(this, "❌ Failed: ${e.message}", Toast.LENGTH_LONG).show()
                }
            }
        }.start()
    }
}
