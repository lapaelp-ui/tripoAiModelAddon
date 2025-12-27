bl_info = {
    "name": "Tripo AI Auto Character Generator",
    "author": "lapaelp",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Tripo AI",
    "description": "Generate, Auto-Rig & Animate 3D Character from Image Texture Node",
    "category": "3D View",
}

import bpy
import os
import time
import mimetypes
import requests
from urllib.parse import urlparse


# ---------------------------------------------------------
# Tripo API endpoints & 기본 설정
# ---------------------------------------------------------
UPLOAD_ENDPOINT   = "https://api.tripo3d.ai/v2/openapi/upload/sts"
TASK_ENDPOINT     = "https://api.tripo3d.ai/v2/openapi/task"
BALANCE_ENDPOINT  = "https://api.tripo3d.ai/v2/openapi/user/balance"

DEFAULT_OUTPUT_FOLDER = os.path.join(os.path.expanduser("~"), "tripo_models")
MODEL_VERSION = "v3.0-20250812"


# ---------------------------------------------------------
# API Key 가져오기 (Scene 프로퍼티에서)
# ---------------------------------------------------------
def get_api_key():
    props = getattr(bpy.context.scene, "tripo_props", None)
    if props is None:
        raise RuntimeError("Tripo properties not found on scene.")
    key = props.api_key.strip()
    if not key:
        raise RuntimeError("Please enter your Tripo API key in the Tripo AI panel.")
    return key


# ---------------------------------------------------------
# Shader Editor에서 활성 Image Texture 노드의 이미지 파일 경로
# ---------------------------------------------------------
def get_image_from_active_image_node():
    screen = bpy.context.window.screen

    shader_space = None
    for area in screen.areas:
        if area.type == "NODE_EDITOR":
            for space in area.spaces:
                if space.type == "NODE_EDITOR" and getattr(space, "tree_type", "") == 'ShaderNodeTree':
                    shader_space = space
                    break
        if shader_space:
            break

    if not shader_space:
        raise RuntimeError("Shader Editor must be open.")

    node_tree = shader_space.node_tree
    if not node_tree:
        raise RuntimeError("No node tree found. Please select a material.")

    node = node_tree.nodes.active
    if not node or node.type != "TEX_IMAGE" or not node.image:
        raise RuntimeError("Please select an Image Texture node with an image.")

    img = node.image
    path = bpy.path.abspath(img.filepath)

    if not path or not os.path.exists(path):
        raise RuntimeError("Only external image files are supported. Please save the image to a file.")
    return path


# ---------------------------------------------------------
# Tripo API: 업로드 / 태스크 / 밸런스
# ---------------------------------------------------------
def upload_image_to_tripo(image_path):
    mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    headers = {"Authorization": f"Bearer {get_api_key()}"}

    files = {
        "file": (os.path.basename(image_path), open(image_path, "rb"), mime_type),
    }

    print("[TRIPO] Uploading image...")
    resp = requests.post(UPLOAD_ENDPOINT, headers=headers, files=files, timeout=120)
    resp.raise_for_status()

    data = resp.json()
    print("[TRIPO] Upload response:", data)

    if data.get("code") != 0:
        raise RuntimeError(f"Upload failed: {data}")

    return mime_type, data["data"]["image_token"]


def start_image_to_model_task(mime_type, image_token):
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }

    body = {
        "type": "image_to_model",
        "model_version": MODEL_VERSION,
        "file": {
            "type": mime_type,
            "file_token": image_token
        },
        "texture": True,
        "pbr": True,
    }

    print("[TRIPO] Requesting image_to_model task...")
    resp = requests.post(TASK_ENDPOINT, headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    print("[TRIPO] image_to_model response:", data)

    if data.get("code") != 0:
        raise RuntimeError(f"image_to_model failed: {data}")

    return data["data"]["task_id"]


def poll_task_until_done(task_id, poll_interval=5):
    headers = {"Authorization": f"Bearer {get_api_key()}"}
    url = f"{TASK_ENDPOINT}/{task_id}"

    while True:
        resp = requests.get(url, headers=headers, timeout=60)
        resp.raise_for_status()

        data = resp.json()
        d = data.get("data", {}) or {}

        status = d.get("status")
        print(f"[TRIPO] Task {task_id} status = {status}")

        if status == "success":
            return d
        if status in ("failed", "cancelled", "expired", "banned"):
            raise RuntimeError(f"Task failed: {data}")

        time.sleep(poll_interval)


def start_rig_task(task_id):
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }

    body = {
        "type": "animate_rig",
        "original_model_task_id": task_id,
        "out_format": "glb",
    }

    print("[TRIPO] animate_rig request:", body)
    resp = requests.post(TASK_ENDPOINT, headers=headers, json=body, timeout=120)

    resp.raise_for_status()
    data = resp.json()
    print("[TRIPO] animate_rig response:", data)

    if data.get("code") != 0:
        raise RuntimeError(f"animate_rig failed: {data}")

    return data["data"]["task_id"]


def start_retarget_task(rig_task_id, animation):
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }

    body = {
        "type": "animate_retarget",
        "original_model_task_id": rig_task_id,
        "out_format": "glb",
        "animation": animation,
    }

    print("[TRIPO] animate_retarget request:", body)
    resp = requests.post(TASK_ENDPOINT, headers=headers, json=body, timeout=120)

    resp.raise_for_status()
    data = resp.json()
    print("[TRIPO] animate_retarget response:", data)

    if data.get("code") != 0:
        raise RuntimeError(f"animate_retarget failed: {data}")

    return data["data"]["task_id"]


def download_model(model_url, output_dir):
    abs_dir = bpy.path.abspath(output_dir) if output_dir else DEFAULT_OUTPUT_FOLDER
    os.makedirs(abs_dir, exist_ok=True)

    path = urlparse(model_url).path
    ext = os.path.splitext(path)[1] or ".glb"

    save_path = os.path.join(
        abs_dir,
        f"tripo_{time.strftime('%Y%m%d_%H%M%S')}{ext}"
    )

    print(f"[TRIPO] Downloading model to: {save_path}")
    r = requests.get(model_url, timeout=300)
    r.raise_for_status()

    with open(save_path, "wb") as f:
        f.write(r.content)

    return save_path


def import_model_to_blender(path):
    ext = os.path.splitext(path)[1].lower()
    print(f"[Blender] Importing model: {path}")

    if ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        bpy.ops.import_scene.gltf(filepath=path)


def fetch_balance():
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }

    resp = requests.get(BALANCE_ENDPOINT, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    print("[TRIPO] Balance response:", data)

    if data.get("code") != 0:
        raise RuntimeError(f"Balance API failed: {data}")

    bal_data = data.get("data", {}) or {}
    return bal_data.get("balance", 0), bal_data.get("frozen", 0)


# ---------------------------------------------------------
# Scene Properties
# ---------------------------------------------------------
class TRIPO_Props(bpy.types.PropertyGroup):
    # 🔑 API Key (패널에서 입력, ●●● 로 마스킹)
    api_key: bpy.props.StringProperty(
        name="API Key",
        description="Tripo API key (starts with tsk_...)",
        default="",
        subtype='PASSWORD',
    )

    # Humanoid-only 옵션들
    do_rig: bpy.props.BoolProperty(
        name="Auto Rig (Humanoid)",
        description="Auto rig character – works only for humanoid-like models.",
        default=False,
    )

    do_animate: bpy.props.BoolProperty(
        name="Auto Animate (Humanoid)",
        description="Add animation – requires a humanoid rigged model.",
        default=False,
    )

    # 🔥 Animation preset – Enum 드롭다운
    animation_preset: bpy.props.EnumProperty(
        name="Animation Preset",
        description="Choose a humanoid animation preset.",
        items=[
            ("preset:idle", "Idle", "Idle loop"),
            ("preset:walk", "Walk", "Walking animation"),
            ("preset:run",  "Run",  "Running animation"),
            ("preset:jump", "Jump", "Jump animation"),
        ],
        default="preset:walk",
    )

    output_dir: bpy.props.StringProperty(
        name="Output Folder",
        description="Where to save downloaded models (leave empty to use default)",
        default="",
        subtype='DIR_PATH',
    )

    balance: bpy.props.IntProperty(
        name="Balance",
        description="Tripo wallet balance",
        default=-1,  # -1 = unknown
    )

    frozen: bpy.props.IntProperty(
        name="Frozen",
        description="Frozen balance",
        default=0,
    )


# ---------------------------------------------------------
# Operators
# ---------------------------------------------------------
class TRIPO_OT_generate(bpy.types.Operator):
    bl_idname = "tripo.generate"
    bl_label = "Generate Character"

    def execute(self, context):
        props = context.scene.tripo_props

        try:
            image_path = get_image_from_active_image_node()

            mime_type, image_token = upload_image_to_tripo(image_path)

            gen_task_id = start_image_to_model_task(mime_type, image_token)
            gen_task_data = poll_task_until_done(gen_task_id)

            output = gen_task_data.get("output", {}) or {}
            model_url = (
                output.get("pbr_model")
                or output.get("model")
                or output.get("glb")
                or output.get("fbx")
                or output.get("url")
                or output.get("model_url")
            )

            if not model_url:
                raise RuntimeError(f"Cannot find model_url in generation output: {output}")

            final_url = model_url
            rig_task_id = None

            # Rig (옵션)
            if props.do_rig or props.do_animate:
                rig_task_id = start_rig_task(gen_task_id)
                rig_task_data = poll_task_until_done(rig_task_id)

                rig_output = rig_task_data.get("output", {}) or {}
                rig_model_url = (
                    rig_output.get("pbr_model")
                    or rig_output.get("model")
                    or rig_output.get("glb")
                )
                if not rig_model_url:
                    raise RuntimeError(f"Cannot find model_url in rig output: {rig_output}")

                final_url = rig_model_url

            # Animate (옵션)
            if props.do_animate and rig_task_id:
                # EnumProperty 값이 그대로 "preset:walk" 형태라 바로 사용 가능
                anim_preset = props.animation_preset
                anim_task_id = start_retarget_task(rig_task_id, anim_preset)
                anim_task_data = poll_task_until_done(anim_task_id)

                anim_output = anim_task_data.get("output", {}) or {}
                anim_model_url = (
                    anim_output.get("pbr_model")
                    or anim_output.get("model")
                    or anim_output.get("glb")
                )
                if not anim_model_url:
                    raise RuntimeError(f"Cannot find model_url in animation output: {anim_output}")

                final_url = anim_model_url

            output_dir = props.output_dir if props.output_dir.strip() else DEFAULT_OUTPUT_FOLDER

            model_path = download_model(final_url, output_dir)
            import_model_to_blender(model_path)

            self.report({'INFO'}, f"Done! Saved to {model_path}")

        except Exception as e:
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class TRIPO_OT_check_balance(bpy.types.Operator):
    bl_idname = "tripo.check_balance"
    bl_label = "Check Balance"

    def execute(self, context):
        props = context.scene.tripo_props
        try:
            balance, frozen = fetch_balance()
            props.balance = balance
            props.frozen = frozen
            self.report({'INFO'}, f"Balance: {balance}, Frozen: {frozen}")
        except Exception as e:
            self.report({'ERROR'}, str(e))
        return {'FINISHED'}


# ---------------------------------------------------------
# UI Panel
# ---------------------------------------------------------
class TRIPO_PT_panel(bpy.types.Panel):
    bl_label = "Tripo AI"
    bl_idname = "TRIPO_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tripo AI"

    def draw(self, context):
        layout = self.layout
        props = context.scene.tripo_props

        # 🔑 API Key 박스
        box = layout.box()
        box.label(text="API Key")
        row = box.row()
        row.prop(props, "api_key", text="")

        layout.separator()

        # ℹ️ Info box
        info = layout.box()
        info.label(text="Info", icon="INFO")

        info.label(text="Image Input")
        info.label(text="• Select the Image Texture node you want to use")

        info.separator()

        info.label(text="Auto Rig / Animate")
        info.label(text="• Works only for humanoid characters")


        layout.separator()
        layout.label(text="Image → 3D Character")

        col = layout.column(align=True)
        col.prop(props, "do_rig")
        col.prop(props, "do_animate")
        col.prop(props, "animation_preset")

        layout.separator()

        # Wallet Balance
        row = layout.row(align=True)
        if props.balance >= 0:
            row.label(text=f"Credits: {props.balance}")
        else:
            row.label(text="Credits: (unknown)")
        row.operator("tripo.check_balance", text="", icon="FILE_REFRESH")

        layout.separator()

        layout.label(text="Output")
        layout.prop(props, "output_dir")

        layout.separator()
        layout.operator("tripo.generate", icon="PLAY")


# ---------------------------------------------------------
# Register
# ---------------------------------------------------------
classes = (
    TRIPO_Props,
    TRIPO_OT_generate,
    TRIPO_OT_check_balance,
    TRIPO_PT_panel,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.tripo_props = bpy.props.PointerProperty(type=TRIPO_Props)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.tripo_props

