from app.models.activity_log import ActivityLog


def create_activity_log(
    db,
    user,
    action,
    module,
    target_id=None,
    target_name=None,
    description=None
):

    log = ActivityLog(

        user_id=user.id,

        action=action,

        module=module,

        target_id=target_id,

        target_name=target_name,

        description=description,

    )


    db.add(log)