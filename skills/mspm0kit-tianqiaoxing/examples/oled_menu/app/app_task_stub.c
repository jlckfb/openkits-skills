#include "app_task_stub.h"
static const AppTaskDef *current_app = NULL;
void app_task_start(const AppTaskDef *app) { current_app = app; if (app && app->init) app->init(); }
void app_task_stop(void) { if (current_app && current_app->on_exit) current_app->on_exit(); current_app = NULL; }
void app_task_tick(void) { if (current_app && current_app->tick) current_app->tick(); }
bool app_task_is_active(void) { return current_app != NULL; }
AppState app_task_get_state(void) { return current_app ? APP_STATE_RUNNING : APP_STATE_IDLE; }
