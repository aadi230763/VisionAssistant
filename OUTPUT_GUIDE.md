# Terminal Output Guide

## 🎨 Clean, Color-Coded Output

The terminal now uses emojis and clear formatting for easy reading:

### Startup Messages
```
============================================================
🎯 VISION-TO-VOICE ASSISTANT
============================================================

🔍 Initializing depth estimation...
✅ Depth estimation enabled
📹 Camera opened successfully
```

---

### Frame Processing
```
============================================================
📹 Frame 15
============================================================
```
Each processed frame is clearly marked with a separator.

---

### Object Detection with Depth

Objects are shown with **color-coded emojis** based on distance:

```
  🔴 PERSON: 0.15 [very_close] → ahead    ← DANGER!
  🟠 CHAIR: 0.35 [close] → left           ← Close by
  🟡 TABLE: 0.55 [moderate] → right       ← Several steps
  🟢 WALL: 0.80 [far] → ahead             ← Background
```

#### Emoji Legend:
- 🔴 **VERY_CLOSE** (0.00-0.24) - Within arm's reach, urgent!
- 🟠 **CLOSE** (0.25-0.44) - A few steps away
- 🟡 **MODERATE** (0.45-0.69) - Several steps away
- 🟢 **FAR** (0.70-1.00) - Background, not immediate

---

### AI Responses
```
💬 AI: A person is several steps ahead on your right.
🔊 Speaking: A person is several steps ahead on your right.
```

---

### Scene Status
```
⏭️  Scene unchanged, skipping AI
```
When nothing has changed, AI processing is skipped.

---

### Urgent Hazard Alert
```
🚨 URGENT: Very close hazard detected!
  🔴 PERSON: 0.18 [very_close] → ahead
  
💬 AI: Warning. Person very close directly ahead. Stop immediately.
🔊 Speaking: Warning. Person very close directly ahead. Stop immediately.
```

---

## 📊 Reading the Output

### Example Frame:
```
============================================================
📹 Frame 45
============================================================
  🟠 PERSON: 0.35 [close] → left
  🟡 CHAIR: 0.52 [moderate] → ahead
  🟢 TABLE: 0.78 [far] → right
```

**What this tells you:**
1. **Person**: 0.35 depth (close), positioned to the left
2. **Chair**: 0.52 depth (moderate), straight ahead
3. **Table**: 0.78 depth (far), to the right

---

## 🎯 What to Look For

### ✅ Good Signs:
- Depth values changing as objects move
- 🔴 for very close objects
- 🚨 URGENT messages for hazards
- Clear AI guidance with direction

### ⚠️ Warning Signs:
- All objects showing same depth value
- No depth emojis appearing
- "depth estimation failed" message

---

## 🔇 Reducing Output Further

If you want even less output, edit `.env`:

```env
# Reduce frame processing frequency
PROCESS_EVERY_N_FRAMES=30  # Process fewer frames

# Increase cooldown
NARRATION_COOLDOWN_S=5     # Speak less often
```

---

## 🧪 Testing the Output

### Move an object closer to camera:
```
Frame 15: 🟢 CUP: 0.75 [far] → ahead
Frame 30: 🟡 CUP: 0.55 [moderate] → ahead
Frame 45: 🟠 CUP: 0.30 [close] → ahead
Frame 60: 🔴 CUP: 0.18 [very_close] → ahead
          🚨 URGENT: Very close hazard detected!
```

You should see the emoji change: 🟢 → 🟡 → 🟠 → 🔴

---

## 📝 Output Comparison

### Before (Cluttered):
```
[app] processing frame 15
Using cache found in /Users/...
[depth_map] min=0.000, max=1.000, mean=0.693, std=0.309
[depth_bbox] median=0.540, mean=0.484, std=0.399, range=[0.001-1.000]
[depth] person: depth=0.540 → MODERATE (ahead)
[depth] Frame depth values: person=0.540
[vertex] A person is several steps ahead.
[tts] speaking: A person is several steps ahead.
```

### After (Clean):
```
============================================================
📹 Frame 15
============================================================
  🟡 PERSON: 0.54 [moderate] → ahead

💬 AI: A person is several steps ahead.
🔊 Speaking: A person is several steps ahead.
```

**Much cleaner!** ✨

---

## 🎨 Terminal Colors

For best experience, use a terminal with emoji support:
- ✅ macOS Terminal (default)
- ✅ iTerm2
- ✅ Windows Terminal
- ✅ VS Code integrated terminal

---

## Summary

The output now shows:
1. **Clear frame separators** (====)
2. **Emoji distance indicators** (🔴🟠🟡🟢)
3. **Concise depth values** (0.54)
4. **Direction info** (left/right/ahead)
5. **AI and speech clearly marked** (💬 🔊)
6. **Urgent alerts stand out** (🚨)

Everything is **clean, organized, and easy to scan**! 🎉
