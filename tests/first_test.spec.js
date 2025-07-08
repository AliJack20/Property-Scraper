const{test,expect} =  require('@playwright/test')

test('Launch Application', async({page}) => {

    await page.goto('https://parabank.parasoft.com/parabank/index.htm;jsessionid=388B6D06B29F69F29865C2EDB0BBAD48');
    await expect(page).toHaveTitle('ParaBank | Welcome | Online Banking')
})