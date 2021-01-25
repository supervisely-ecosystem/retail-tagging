import supervisely_lib as sly
import globals as ag
import requests
import references
import cache


def assign(api, figure_id, tag_meta, remove_duplicates=True):
    if remove_duplicates is True:
        delete(api, figure_id, tag_meta)
    api.advanced.add_tag_to_object(tag_meta.sly_id, figure_id)


def delete(api, figure_id, tag_meta):
    try:
        tags_json = api.advanced.get_object_tags(figure_id)
        tags = sly.TagCollection.from_json(tags_json, ag.meta.tag_metas)
        for tag in tags:
            if tag.meta.sly_id == tag_meta.sly_id:
                api.advanced.remove_tag_from_object(tag_meta.sly_id, figure_id, tag.sly_id)
    except requests.exceptions.HTTPError as error:
        if error.response.status_code == 404:
            return None
        else:
            raise error


def change_tag(api: sly.Api, task_id, context, state, app_logger, action_figure, action_reference):
    tag_meta = ag.meta.get_tag_meta(ag.reference_tag_name)
    userId = context["userId"]
    figure_id = context["figureId"]
    image_id = context["imageId"]

    image_info = api.image.get_info_by_id(image_id)
    field_value = image_info.meta[ag.field_name]
    ann = cache.get_annotation(image_id)
    selected_label = ann.get_label_by_id(figure_id)

    if selected_label is None:
        raise KeyError(f"Figure with id {figure_id} is not found in annotation")
    if selected_label.obj_class.name == ag.target_class_name:
        action_figure(api, figure_id, tag_meta)
        action_reference(field_value, image_info, selected_label)
    elif selected_label.obj_class.name == ag.multiselect_class_name:
        for idx, label in enumerate(ann.labels):
            if label.geometry.sly_id == figure_id:
                continue
            if label.geometry.to_bbox().intersects_with(selected_label.geometry.to_bbox()):
                action_figure(api, label.geometry.sly_id, tag_meta)
                action_reference(field_value, image_info, label)
    references.refresh_grid(userId, field_value)


@ag.app.callback("assign_tag")
@sly.timeit
def assign_tag(api: sly.Api, task_id, context, state, app_logger):
    change_tag(api, task_id, context, state, app_logger, assign, references.add)


@ag.app.callback("delete_tag")
@sly.timeit
def delete_tag(api: sly.Api, task_id, context, state, app_logger):
    change_tag(api, task_id, context, state, app_logger, delete, references.delete)