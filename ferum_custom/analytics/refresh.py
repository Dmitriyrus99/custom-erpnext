from ferum_custom.ferum_custom.domain.analytics import application as analytics_app


def refresh_all_materialized_views():
    analytics_app.refresh_all_materialized_views()
