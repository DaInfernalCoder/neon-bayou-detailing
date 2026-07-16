#!/usr/bin/env python3
"""Responsive browser smoke test for the Neon Bayou website."""

from __future__ import annotations

from playwright.sync_api import sync_playwright


URL = "http://127.0.0.1:4174"
PHONE = "tel:+13466456236"
SCHEDULER = "https://cal.com/sumitdatta/auto-detail-service"


def main() -> None:
    failures: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()

        for width, height in ((1440, 1000), (1024, 900), (390, 844)):
            page = browser.new_page(viewport={"width": width, "height": height})
            console_errors: list[str] = []
            page_errors: list[str] = []
            page.on(
                "console",
                lambda message: console_errors.append(message.text)
                if message.type == "error"
                else None,
            )
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.goto(URL, wait_until="load")
            page.wait_for_timeout(500)

            metrics = page.evaluate(
                """([phone, scheduler]) => ({
                    viewport: innerWidth,
                    scrollWidth: document.documentElement.scrollWidth,
                    h1: document.querySelectorAll("h1").length,
                    images: [...document.images].map(image => ({
                        src: image.getAttribute("src"),
                        complete: image.complete,
                        width: image.naturalWidth
                    })),
                    headerBackground:
                        getComputedStyle(document.querySelector(".site-header")).backgroundColor,
                    phoneLinks: document.querySelectorAll(`a[href="${phone}"]`).length,
                    schedulerLinks:
                        document.querySelectorAll(`a[href="${scheduler}"]`).length,
                    forms: document.querySelectorAll("form").length,
                    emails: document.querySelectorAll('a[href^="mailto:"]').length,
                    wake: Boolean(document.querySelector(".clean-wake")),
                    sticky: Boolean(document.querySelector(".mobile-sticky")),
                    overflowing: [...document.querySelectorAll("body *")]
                        .map(element => {
                            const rect = element.getBoundingClientRect();
                            return {
                                tag: element.tagName,
                                className: element.className?.baseVal || element.className || "",
                                left: Math.round(rect.left),
                                right: Math.round(rect.right),
                                width: Math.round(rect.width)
                            };
                        })
                        .filter(item => item.left < -1 || item.right > innerWidth + 1)
                        .slice(0, 12)
                })""",
                [PHONE, SCHEDULER],
            )
            print(f"{width}px: {metrics}")

            if metrics["scrollWidth"] > metrics["viewport"]:
                failures.append(f"{width}px has horizontal overflow")
            if metrics["h1"] != 1:
                failures.append(f"{width}px has {metrics['h1']} H1 elements")
            if metrics["phoneLinks"] < 5 or metrics["schedulerLinks"] < 5:
                failures.append(f"{width}px is missing repeated telephone or appointment paths")
            if metrics["forms"] or metrics["emails"]:
                failures.append(f"{width}px includes a public form or email link")
            if any(not image["complete"] or image["width"] < 1 for image in metrics["images"]):
                failures.append(f"{width}px has an incomplete image")
            if metrics["headerBackground"] in {"rgba(0, 0, 0, 0)", "transparent"}:
                failures.append(f"{width}px header has no independent background")
            if not metrics["wake"] or not metrics["sticky"]:
                failures.append(f"{width}px is missing a required identity or contact element")

            reveal_count = page.locator(".reveal").count()
            for index in range(reveal_count):
                page.locator(".reveal").nth(index).scroll_into_view_if_needed()
                page.wait_for_timeout(25)
            visible_count = page.locator(".reveal.visible").count()
            print(f"reveal elements: {visible_count}/{reveal_count}")
            if visible_count != reveal_count:
                failures.append(f"{width}px reveal sequence left hidden content")

            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(150)

            if width == 1440:
                page.locator(".site-header").screenshot(path="/tmp/neon-bayou-header.png")
                page.screenshot(path="/tmp/neon-bayou-desktop.png", full_page=True)

            if width == 390:
                page.locator(".menu-toggle").click()
                expanded = page.locator(".menu-toggle").get_attribute("aria-expanded")
                nav_open = page.locator("#site-nav").evaluate(
                    "element => element.classList.contains('open')"
                )
                print(f"mobile menu: open={nav_open}; aria-expanded={expanded}")
                if expanded != "true" or not nav_open:
                    failures.append("mobile menu did not enter its visible state")
                page.locator(".menu-toggle").click()

                page.locator("#questions details:first-child summary").click()
                question_open = page.locator("#questions details:first-child").get_attribute("open")
                print(f"question panel opens: {question_open is not None}")
                if question_open is None:
                    failures.append("question panel did not open")

                page.screenshot(path="/tmp/neon-bayou-mobile.png", full_page=True)

            if console_errors:
                failures.append(f"{width}px console errors: {console_errors}")
            if page_errors:
                failures.append(f"{width}px page errors: {page_errors}")
            page.close()

        browser.close()

    if failures:
        raise SystemExit("QA failures:\n- " + "\n- ".join(failures))
    print("PASS browser QA")


if __name__ == "__main__":
    main()
