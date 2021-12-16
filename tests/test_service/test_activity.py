from datetime import datetime

from pytest import mark

from app.service.activity import cal_portfolio_ranking_in_activity_by_date

pytestmark = mark.asyncio


@mark.skip
async def test_cal_portfolio_ranking_in_activity_by_date(
    fixture_client, fixture_db, fixture_settings, fixture_activity, fixture_portfolio
):
    fixture_portfolio["activity"] = fixture_activity["_id"]
    await fixture_db[fixture_settings.db.DB_NAME][
        fixture_settings.collections.PORTFOLIO
    ].update_one(
        {"_id": fixture_portfolio["_id"]},
        {"$set": {"activity": fixture_activity["_id"]}},
    )
    cal_date = datetime.strptime("2020-09-01", "%Y-%m-%d")
    result = await cal_portfolio_ranking_in_activity_by_date(
        fixture_db, fixture_activity["_id"], cal_date
    )
    assert len(result) == 1
