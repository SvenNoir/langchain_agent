from route import api


def setup_routes(app, env):
    app.include_router(
        api.router
    )

    @app.get("/")
    async def read_root():
        return {
            "app_name": env.app_name,
            "app_version": env.app_version,
        }