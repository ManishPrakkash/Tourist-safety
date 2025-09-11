# Tourist Safety Project

## Overview
The Tourist Safety Project aims to enhance the safety and security of tourists through location tracking and emergency communication features. This repository contains the backend server and mobile application components.

## Project Structure
```
/Tourist-safety
│
├── server/
│   ├── server.py          # Main server file
│   └── requirements.txt   # Python dependencies
│
├── simplelocationtracker/  # Mobile app for location tracking
│   └── ...                # App files
│
└── smsreceiverapp/        # SMS receiver application
    └── ...                # App files
```

## Prerequisites
- Python 3.x
- pip (Python package installer)
- Flask (or any other required framework)
- Android Studio (for the mobile app)

## Installation

### Setting Up the Server

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ManishPrakkash/Tourist-safety.git
   cd Tourist-safety/server
   ```

2. **Install dependencies**:
   Make sure you have `requirements.txt` in your server directory. Install the required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Server

3. **Run the server**:
   Execute the following command to start the server:
   ```bash
   python server.py
   ```
   The server will start on `http://127.0.0.1:5000` by default. You can change the port in the `server.py` file if needed.

### Setting Up the Mobile App

4. **Open the mobile app**:
   Navigate to the `simplelocationtracker` directory in Android Studio.

5. **Build and run the app**:
   - Open the project in Android Studio.
   - Ensure you have an Android emulator running or a physical device connected.
   - Click on the "Run" button to build and deploy the app.

## Usage
- Once the server is running, the mobile app will communicate with the server to track the user's location and send emergency messages.
- Ensure that you have permissions set up in your mobile app for location access and SMS sending.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or features.
