#!/data/data/com.termux/files/usr/bin/bash
clear
echo "================================================"
echo "   MATRIX CONSOLE - ONE-TIME AUTO INSTALLER"
echo "================================================"
echo ""

# 1. Install required packages
echo "[1/6] Installing packages... (this takes a minute)"
pkg update -y -q
pkg install -y -q python tmux git termux-api

echo "[2/6] Installing python libraries..."
pip install -q pyrogram tgcrypto --break-system-packages

# 2. Ask for credentials using popup boxes
echo "[3/6] Asking for your Telegram API credentials..."
API_ID=$(termux-dialog -t "API ID" -i "Enter your Telegram API ID (number)" | grep -o '"text": *"[^"]*"' | cut -d'"' -f4)
API_HASH=$(termux-dialog -t "API HASH" -i "Enter your Telegram API HASH" | grep -o '"text": *"[^"]*"' | cut -d'"' -f4)

if [ -z "$API_ID" ] || [ -z "$API_HASH" ]; then
    termux-dialog -t "Error" -i "API ID/HASH empty. Run install again." > /dev/null
    exit 1
fi

# 3. Download main script and insert credentials
echo "[4/6] Downloading script and inserting your credentials..."
mkdir -p ~/matrix
curl -sL -o ~/matrix/script.py "https://raw.githubusercontent.com/saransh098a-ops/matrix-bott/main/script_template.py"
sed -i "s/^API_ID.*/API_ID   = $API_ID/" ~/matrix/script.py
sed -i "s/^API_HASH.*/API_HASH = \"$API_HASH\"/" ~/matrix/script.py

# 4. Create home-screen shortcut scripts
echo "[5/6] Creating home-screen shortcuts..."
mkdir -p ~/.shortcuts

cat > ~/.shortcuts/Matrix_Start.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
tmux kill-session -t matrix 2>/dev/null
tmux new-session -d -s matrix "cd ~/matrix && while true; do python3 script.py; sleep 3; done"
sleep 1
tmux attach -t matrix
EOF
chmod +x ~/.shortcuts/Matrix_Start.sh

cat > ~/.shortcuts/Matrix_View.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
tmux attach -t matrix || echo "Not running. Tap Matrix_Start first."
EOF
chmod +x ~/.shortcuts/Matrix_View.sh

cat > ~/.shortcuts/Matrix_Stop.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
tmux kill-session -t matrix 2>/dev/null
termux-wake-unlock
echo "Matrix stopped."
sleep 1
EOF
chmod +x ~/.shortcuts/Matrix_Stop.sh

# 5. Setup auto-start on boot
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start-matrix.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
tmux new-session -d -s matrix "cd ~/matrix && while true; do python3 script.py; sleep 3; done"
termux-notification -i 200 \
  -t "⚡ Matrix Console Controls" \
  -c "Tap buttons below to control your script" \
  --ongoing \
  --button1 "Start" --button1-action "bash ~/.shortcuts/Matrix_Start.sh" \
  --button2 "View"  --button2-action "bash ~/.shortcuts/Matrix_View.sh" \
  --button3 "Stop"  --button3-action "bash ~/.shortcuts/Matrix_Stop.sh"
EOF
chmod +x ~/.termux/boot/start-matrix.sh

# 6. Start it now for the first time
echo "[6/6] Starting Matrix Console now..."
termux-wake-lock
tmux kill-session -t matrix 2>/dev/null
tmux new-session -d -s matrix "cd ~/matrix && while true; do python3 script.py; sleep 3; done"

termux-dialog -t "DONE!" -i "Setup complete! Opening login screen now... If asked for Phone Number, enter it with country code (e.g. +91xxxxxxxxxx). Then enter the OTP code Telegram sends you." > /dev/null

# Create a persistent notification with Start/View/Stop buttons
termux-notification -i 200 \
  -t "⚡ Matrix Console Controls" \
  -c "Tap buttons below to control your script" \
  --ongoing \
  --button1 "Start" --button1-action "bash ~/.shortcuts/Matrix_Start.sh" \
  --button2 "View"  --button2-action "bash ~/.shortcuts/Matrix_View.sh" \
  --button3 "Stop"  --button3-action "bash ~/.shortcuts/Matrix_Stop.sh"

echo ""
echo "================================================"
echo "  ✅ INSTALL COMPLETE!"
echo "  Dashboard: http://localhost:8080"
echo ""
echo "  >>> CONTROLS <<<"
echo "  Check your NOTIFICATION BAR (swipe down from"
echo "  top of screen) - you'll see 3 buttons there:"
echo "  Start / View / Stop"
echo "  (These stay there permanently)"
echo ""
echo "  >>> FIRST TIME LOGIN <<<"
echo "  Opening Telegram login screen in 3 seconds..."
echo "  - 'Enter phone number' aaye to apna number"
echo "    country code ke saath likho (e.g. +91...)"
echo "    aur Enter dabao"
echo "  - Phir Telegram pe aaya OTP code type karo"
echo "    aur Enter dabao"
echo "  - Ye SIRF EK BAAR hoga."
echo "================================================"
sleep 3
tmux attach -t matrix
