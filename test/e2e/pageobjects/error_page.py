from test.e2e.pageobjects.base_page import BasePage
from playwright.sync_api import Page, expect


class ErrorPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page, page.locator("article"), "Error Page")
        self.error_code = self.page_locator.locator("#status-code")
        self.error_description = self.page_locator.locator("#error-message")
        self.page = page

    # Expectations
    def should_have_error_text(self, code, description):
        expect(
            self.error_code,
            f"Error code displayed on {self.page_name} was incorrect",
        ).to_have_text(code)
        expect(
            self.error_description,
            f"Error description displayed on {self.page_name} was incorrect",
        ).to_have_text(description)

    def should_be_opened(self):
        expect(self.page).to_have_title("error")
