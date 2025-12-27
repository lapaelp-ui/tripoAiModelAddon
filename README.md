# Tripo AI Auto Character Generator — Blender Add-on

Generate 3D characters directly inside Blender from an image texture using **Tripo AI**.  
Optionally apply **auto-rigging (humanoid)** and **auto-animation** using simple presets such as Walk, Run, Idle, or Jump.

This add-on uses the **currently selected Image Texture node** in the Shader Editor as input.

---

## ✨ Features

- Generate a 3D model from a 2D image via Tripo AI
- Processing runs on Tripo servers (no GPU required locally)
- Automatically imports generated model back into Blender
- Optional humanoid-only features:
  - Auto Rig
  - Auto Animate (preset-driven)
- Animation presets included:
  - Idle
  - Walk
  - Run
  - Jump
- Tripo wallet balance viewer
- Custom output directory selection
- Full workflow inside Blender UI

---

## 🧩 Requirements

- Blender 4.0 or newer
- Internet connection
- A valid Tripo AI API key (`tsk_...`)
- Enough Tripo credits for:
  - model generation
  - rigging (optional)
  - animation (optional)

---

## 📦 Installation

1. Download the add-on zip file
2. Open Blender and go to:

   `Edit → Preferences → Add-ons`

3. Click **Install…**
4. Select the zip file
5. Enable:

   **Tripo AI Auto Character Generator**

6. Open the panel from:

   `3D Viewport → N panel → Tripo AI`

---

## 🖼 Image Input

This add-on uses the image from the **active Image Texture node**.

Steps:

1. Open **Shader Editor**
2. Select your material
3. Click the **Image Texture node**
4. Make sure the image is saved to disk (not only packed)

The UI info section reminds you:

- Image input
- Select the image node you want to use
- Auto rig / animate
- Only for humanoid

---

## 🤖 Auto Rig & Auto Animate (Humanoid only)

Auto rigging and animation are designed for:

- humanoid characters
- upright bipedal figures

They may not work properly for:

- animals
- robots
- creatures
- objects
- abstract forms

---

## 🎮 Animation Presets

Provided as a dropdown (no typing required):

- Idle
- Walk
- Run
- Jump

Internally mapped to:

- `preset:idle`
- `preset:walk`
- `preset:run`
- `preset:jump`

---

## 🧭 How to Use

1. Enter your **Tripo API Key**
2. (Optional) choose output folder
3. Check remaining credits using **Check Balance**
4. Select options:

   - Auto Rig (humanoid)
   - Auto Animate (humanoid)
   - Choose animation preset

5. Click:

   **Generate Character**

The add-on will:

- upload image to Tripo
- generate 3D model
- (optional) auto-rig
- (optional) auto-animate
- download the model
- import into Blender

---

## 💰 Wallet & Credits

Click **Check Balance** to display:

- Available balance
- Frozen balance

Each step consumes credits:

- image → 3D model
- rigging
- animation retargeting

Your Tripo plan determines costs.

---

## 🗂 Output Location

Generated models are saved to:

- user-selected directory, or
- default: `~/tripo_models`

Files are automatically imported into the current Blender scene.

---

## ⚠ Troubleshooting

### 403 Forbidden
Possible causes:

- invalid API key
- expired API key
- insufficient credits
- endpoint not allowed in your plan

### Auto rig fails or bones look wrong

- model is likely **not humanoid**
- try:
  - disable Auto Animate
  - run Generate Only
  - use simpler image

### “Please select Image Texture node”

Open Shader Editor → select target node.

---

## 🔐 Legal Notice

This add-on is **not affiliated with, endorsed by, or officially approved by Tripo AI or Tripo3D**.  
It is an independent third-party tool that uses Tripo’s **public API**.

This add-on does **NOT**:

- distribute or embed API keys
- bypass Tripo pricing, quotas, or limits
- re-host Tripo services or models

All AI processing runs on **Tripo servers** and is subject to:

- Tripo Terms of Service
- Tripo pricing & credits policy
- Tripo privacy policy

By using this add-on, you agree that:

- you must provide your own Tripo account & API key
- you are responsible for complying with Tripo’s policies

This software is provided **“as-is”**, without warranty of any kind.  
The author is not liable for any damages, credit use, or account actions arising from its use.

---

## 📄 License

MIT License is recommended. Add your preferred license here.

---

## 📝 Credits

Built for artists who want:

- fast concept character prototyping
- Blender-native AI workflows
- zero-GPU 3D generation

Have fun creating! 🚀
