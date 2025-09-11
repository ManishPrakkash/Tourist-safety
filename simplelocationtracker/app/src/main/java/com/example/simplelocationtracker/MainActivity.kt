package com.example.simplelocationtracker

import android.Manifest
import android.content.pm.PackageManager
import android.location.Location
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.annotation.RequiresPermission
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import com.android.volley.Request
import com.android.volley.toolbox.StringRequest
import com.android.volley.toolbox.Volley
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import android.telephony.SmsManager
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.telephony.TelephonyManager

class MainActivity : AppCompatActivity() {

    private lateinit var fusedLocationClient: FusedLocationProviderClient
    private lateinit var locationText: TextView
    private lateinit var sendBtn: Button

    // Replace with your server (or ngrok) URL
        private val SERVER_URL = " https://92473fdc5dac.ngrok-free.app/update_location"
    private val SMS_PHONE_NUMBER = "7200363858" // SIM2 phone number here

    private val locationPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) @androidx.annotation.RequiresPermission(
            allOf = [android.Manifest.permission.ACCESS_FINE_LOCATION, android.Manifest.permission.ACCESS_COARSE_LOCATION]
        ) { granted ->
            if (granted) getAndSendLocation()
            else Toast.makeText(this, "Location permission denied", Toast.LENGTH_SHORT).show()
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        locationText = findViewById(R.id.locationText)
        sendBtn = findViewById(R.id.sendBtn)

        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)

        // Ask for SMS permission early
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.SEND_SMS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.SEND_SMS), 101)
        }

        sendBtn.setOnClickListener {
            if (ActivityCompat.checkSelfPermission(
                    this, Manifest.permission.ACCESS_FINE_LOCATION
                ) == PackageManager.PERMISSION_GRANTED
            ) {
                getAndSendLocation()
            } else {
                locationPermissionLauncher.launch(Manifest.permission.ACCESS_FINE_LOCATION)
            }
        }
    }

    @RequiresPermission(allOf = [Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION])
    private fun getAndSendLocation() {
        val cts = CancellationTokenSource()
        fusedLocationClient.getCurrentLocation(
            Priority.PRIORITY_HIGH_ACCURACY,
            cts.token
        ).addOnSuccessListener { location: Location? ->
            if (location != null) {
                processLocation(location)
            } else {
                fusedLocationClient.lastLocation.addOnSuccessListener { last: Location? ->
                    if (last != null) processLocation(last)
                    else Toast.makeText(this, "Location not available", Toast.LENGTH_SHORT).show()
                }
            }
        }.addOnFailureListener {
            Toast.makeText(this, "Failed to get location: ${it.message}", Toast.LENGTH_SHORT).show()
        }
    }

    private fun processLocation(location: Location) {
        val lat = location.latitude
        val lon = location.longitude
        locationText.text = "Lat: $lat, Lon: $lon"
        sendLocation(lat, lon)
    }

    private fun sendLocation(lat: Double, lon: Double) {
        if (isInternetAvailable()) {
            sendToServer(lat, lon)
        } else {
            sendLocationSMS(lat, lon)
        }
    }

    private fun sendToServer(lat: Double, lon: Double) {
        val queue = Volley.newRequestQueue(this)

        // try to get device phone number (may be null)
        val tm = getSystemService(TELEPHONY_SERVICE) as TelephonyManager
        var phoneNumber: String? = null
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.READ_PHONE_STATE) == PackageManager.PERMISSION_GRANTED) {
            phoneNumber = tm.line1Number
        }
        if (phoneNumber.isNullOrEmpty()) phoneNumber = "UnknownNumber"

        val req = object : StringRequest(
            Request.Method.POST, SERVER_URL,
            { resp ->
                Log.d("ServerResponse", resp)
                Toast.makeText(this, "✅ Sent to server!", Toast.LENGTH_SHORT).show()
            },
            { err ->
                Log.e("ServerError", err.toString())
                Toast.makeText(this, "❌ Error sending data", Toast.LENGTH_SHORT).show()
            }
        ) {
            override fun getParams(): MutableMap<String, String> {
                return hashMapOf(
                    "latitude" to lat.toString(),
                    "longitude" to lon.toString(),
                    "phone" to phoneNumber!!
                )
            }
        }
        queue.add(req)
    }

    private fun sendLocationSMS(lat: Double, lon: Double) {
        val message = "LAT:$lat,LON:$lon"
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.SEND_SMS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            Toast.makeText(this, "SMS permission not granted", Toast.LENGTH_SHORT).show()
            return
        }
        val smsManager = SmsManager.getDefault()
        smsManager.sendTextMessage(SMS_PHONE_NUMBER, null, message, null, null)
        Toast.makeText(this, "📩 SMS Sent: $message", Toast.LENGTH_SHORT).show()
    }

    private fun isInternetAvailable(): Boolean {
        val cm = getSystemService(CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = cm.activeNetwork ?: return false
        val capabilities = cm.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }
}
