import json
import supervisely_lib as sly

import globals as ag  # application globals
import catalog
import references
import objects_iterator
import batches


@ag.app.callback("manual_selected_image_changed")
def event_next_image(api: sly.Api, task_id, context, state, app_logger):
    user_id = context["userId"]
    cur_image_id = context["imageId"]
    if cur_image_id is None or type(cur_image_id) is not int:
        app_logger.warn("Image Changed event with wrong context", extra={"ui_context": context})
        return

    cur_image_info = api.image.get_info_by_id(cur_image_id)
    field = cur_image_info.meta.get(ag.field_name, None)

    if field is None:
        fields = {
            "fieldNotFound": "Field {!r} not found".format(ag.field_name),
            "fieldValue": "",
            "catalogInfo": {}
        }
    else:
        catalog_info = catalog.index.get(field, None)
        fields = {
            "fieldNotFound": "" if catalog_info is not None else "Key {!r} not found in catalog".format(field),
            "fieldValue": field,
            "catalogInfo": catalog_info,
        }

    api.app.set_field(task_id, "data.user", {user_id: fields}, append=True)
    references.refresh_grid(user_id, field)


def main():
    ag.init()

    data = {}
    data["user"] = {}

    data["catalog"] = {"columns": [], "data": []}
    #data["ownerId"] = ag.owner_id
    data["targetProject"] = {"id": ag.project.id, "name": ag.project.name}
    data["currentMeta"] = {}
    data["fieldName"] = ag.field_name

    state = {}
    state["selectedTab"] = "references"
    state["targetClass"] = ag.target_class_name
    state["multiselectClass"] = ag.multiselect_class_name
    state["user"] = {}
    state["selected"] = {}

    sly.logger.info("Initialize catalog ...")
    catalog.init()
    data["catalog"] = json.loads(catalog.df.to_json(orient="split"))
    data["emptyGallery"] = references.empty_gallery

    sly.logger.info("Initialize batches ...")
    batches.init(data, state)

    ag.app.run(data=data, state=state)


#@TODO: app session owner can switch batches (for validation)
if __name__ == "__main__":
    sly.main_wrapper("main", main)
