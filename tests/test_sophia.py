from bs4 import BeautifulSoup

from univ_oc.parsers.sophia import parse


def test_sophia_event_ad_extracts_2026_oc() -> None:
    html = """
    <html><head><title>イベント｜上智</title></head><body>
    <div class="c-stickyBlock">
      <div class="c-stickyBlock__contents">
        <h2 class="c-decHeading3t4">本学開催の受験生向けイベント<br>【四谷キャンパス・目白聖母キャンパス】</h2>
        <div class="c-scheduleList">
          <dl class="c-scheduleItem">
            <dt>
              <p class="c-scheduleItem__date"><time datetime="2026-08-04">2026.08.04</time></p>
              <p class="c-scheduleItem__time">
                <time class="-start" datetime="2026-08-04">10:00</time>
                <time class="-end" datetime="2026-08-04">16:00</time>
              </p>
            </dt>
            <dd><b>SOPHIA OPEN CAMPUS 2026</b><br>【神・文・外国語・総合グローバル・理工】</dd>
          </dl>
        </div>
      </div>
    </div>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    out = parse(soup, page_url="https://adm.sophia.ac.jp/jpn/event_ad/", reservation_url=None)
    lines = " ".join(out["normalized"]["schedule_lines"])
    assert "2026.08.04" in lines
    assert "理工" in lines
    assert "SOPHIA OPEN CAMPUS 2026" in lines
    cbs = out["normalized"]["campus_block_schedule"]
    assert "四谷キャンパス" in cbs and "目白聖母キャンパス" in cbs
