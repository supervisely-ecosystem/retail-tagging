import os
import supervisely_lib as sly
import globals as ag

user2batches = None
batches = None

empty_gallery = {
    "content": {
        "projectMeta": {},
        "annotations": {},
        "layout": []
    },
    "previewOptions": ag.image_preview_options,
    "options": ag.image_grid_options,
}

user_grid = {}
user_selected = {}
CNT_GRID_COLUMNS = 2


def init(data, state):
    global user2batches, batches, user_grid
    local_path = os.path.join(ag.app.data_dir, ag.user2batches_path.lstrip("/"))
    ag.api.file.download(ag.team_id, ag.user2batches_path, local_path)
    user2batches = sly.json.load_json_file(local_path)

    local_batches_path = os.path.join(ag.app.data_dir, user2batches["batches_path"].lstrip("/"))
    ag.api.file.download(ag.team_id, user2batches["batches_path"], local_batches_path)
    batches = sly.json.load_json_file(local_batches_path)
    batches = {batch["batch_index"]: batch for batch in batches}

    for userLogin, bindices in user2batches["users"].items():
        user_info = ag.api.user.get_member_info_by_login(ag.team_id, userLogin)
        if user_info is None:
            sly.logger.warn(f"User {userLogin} not found in team_id={ag.team_id}")
            continue
        user_id = user_info.id
        user_selected[user_id] = None
        user_grid_items = []
        for bindex in bindices:
            batch = batches[bindex]
            for reference_key, ref_examples in batch["references"].items():
                for reference_info in ref_examples:
                    image_url = reference_info["image_url"]
                    [top, left, bottom, right] = reference_info["bbox"]
                    label = sly.Label(sly.Rectangle(top, left, bottom, right), ag.gallery_meta.get_obj_class("product"))
                    catalog_info = batch["references_catalog_info"][reference_key]
                    figure_id = reference_info["geometry"]["id"]

                    user_grid_items.append({
                        "batchIndex": bindex,  # store for simplicity
                        "labelId": figure_id,  # duplicate for simplicity
                        "url": image_url,
                        "figures": [label.to_json()],
                        "zoomToFigure": {
                            "figureId": figure_id,
                            "factor": 1.2
                        },
                        "catalogInfo": catalog_info
                    })

        user_grid[user_id] = {
            "content": {
                "projectMeta": ag.gallery_meta.to_json(),
                "annotations": {},
                "layout": [[] for i in range(CNT_GRID_COLUMNS)]
            },
            # "previewOptions": ag.image_preview_options,
            "options": ag.image_grid_options,
        }

        for idx, item in enumerate(user_grid_items):
            user_grid[user_id]["content"]["annotations"][item["labelId"]] = item
            user_grid[user_id]["content"]["layout"][idx % CNT_GRID_COLUMNS].append(item["labelId"])

    data["userGrid"] = user_grid
    state["selected"] = {}


# def refresh_grid(user_id, field_value):
#     grid_data = {}
#     card_index = 0
#
#     current_refs = data.get(field_value, {})
#
#     ref_count = 0
#     for ref_image_id, ref_labels_ids in current_refs.items():
#         ref_count += len(ref_labels_ids)
#     if ref_count <= 1:
#         CNT_GRID_COLUMNS = 1
#     elif ref_count <= 6:
#         CNT_GRID_COLUMNS = 2
#     else:
#         CNT_GRID_COLUMNS = 3
#
#     cards_checkboxes = {}
#     grid_layout = [[] for i in range(CNT_GRID_COLUMNS)]
#     for ref_image_id, ref_labels_ids in current_refs.items():
#         image_info = image_by_id[ref_image_id]
#         for label_id in ref_labels_ids:
#             label = label_by_id[label_id]
#             grid_key = str(label_id)
#
#             cards_checkboxes[grid_key] = False
#             grid_data[grid_key] = {
#                 "labelId": grid_key,  # duplicate for simplicity
#                 "url": image_info.full_storage_url,
#                 "figures": [label.to_json()],
#                 "zoomToFigure": {
#                     "figureId": label_id,
#                     "factor": 1.2
#                 }
#             }
#             grid_layout[card_index % CNT_GRID_COLUMNS].append(grid_key)
#             card_index += 1
#
#     fields = {
#         "refCount": ref_count,
#         "totalRefCount": count,
#         "previewRefs": {
#             "content": {
#                 "projectMeta": ag.meta.to_json(),
#                 "annotations": grid_data,
#                 "layout": grid_layout
#             },
#             "previewOptions": ag.image_preview_options,
#             "options": ag.image_grid_options,
#         }
#     }
#     ag.api.app.set_field(ag.task_id, f"data.user.{user_id}", fields, append=True)
#     ag.api.app.set_field(ag.task_id, f"state.user.{user_id}.cardsCheckboxes", cards_checkboxes)



# Example: user2batches
# {
# 	"batches_path": "/reference_items/batches_aguas.json",
# 	"users": {
# 		"admin": [
# 			0,
# 			1,
# 			2,
# 			3
# 		],
# 		"quantigo18": [
# 			4,
# 			5,
# 			6,
# 			7
# 		],
# 		"quantigo19": [
# 			8,
# 			9,
# 			10,
# 			11,
# 			12,
# 			13
# 		],
# 		"quantigo20": [
# 			14,
# 			15,
# 			16,
# 			17,
# 			18,
# 			19,
# 			20
# 		],
# 		"quantigo21": [
# 			21
# 		]
# 	}
# }