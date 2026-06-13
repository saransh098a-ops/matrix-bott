#!/data/data/com.termux/files/usr/bin/bash
# ============================================
#  MATRIX CONSOLE - AUTO SETUP SCRIPT
#  Yeh script Termux ke andar khud chalega
# ============================================

API_ID="$1"
API_HASH="$2"

echo "📦 Step 1: Installing packages (one time only)..."
pkg update -y
pkg install -y python tmux git

echo "📦 Step 2: Installing python libraries..."
pip install pyrogram tgcrypto --break-system-packages

echo "📥 Step 3: Downloading your script..."
mkdir -p ~/matrix
curl -sL -o ~/matrix/script.py "https://raw.githubusercontent.com/saransh098a-ops/matrix-bott/main/script_template.py"

echo "🔑 Step 4: Inserting your API ID and HASH..."
sed -i "s/^API_ID.*/API_ID   = $API_ID/" ~/matrix/script.py
sed -i "s/^API_HASH.*/API_HASH = \"$API_HASH\"/" ~/matrix/script.py

echo "🔓 Step 4.5: Enabling wake-lock (stops Android from killing Termux)..."
termux-wake-lock

echo "🛑 Step 5: Stopping old session (if any)..."
tmux kill-session -t matrix 2>/dev/null

echo "🚀 Step 6: Starting script in tmux session 'matrix'..."
tmux new-session -d -s matrix "cd ~/matrix && while true; do python3 script.py; sleep 3; done"

echo "🔁 Step 7: Setting up auto-start on phone reboot..."
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start-matrix.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
tmux new-session -d -s matrix "cd ~/matrix && while true; do python3 script.py; sleep 3; done"
EOF
chmod +x ~/.termux/boot/start-matrix.sh

echo ""
echo "✅✅✅ SETUP COMPLETE! ✅✅✅"
echo "Open browser: http://localhost:8080"
echo "To see the running script anytime, run: tmux attach -t matrix"
