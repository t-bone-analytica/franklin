const puppeteer = require('puppeteer');

async function checkPropertyClass( propertyId )
{
    var propertyClass;
    try {

        // Browser setup
        const browser = await puppeteer.launch( {headless: false} );
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.59 Safari/537.36');

        // Navigate to the search form
        await page.goto( 'http://property.franklincountyauditor.com/_web/search/commonsearch.aspx?mode=parid' );
        await page.waitForSelector('#inpParid');

        // Fill in the serch form with the Property ID being checked
        await page.evaluate((propertyId) => {
            document.querySelector('#inpParid').value = propertyId;
        }, propertyId);

        // Submit the search form
        await page.$eval('#frmMain', form => form.submit());
        await page.waitForNavigation();

        const res = await page.$eval('#datalet_div_3 td.DataletData', function(heading) {
            return heading.innerText;
        }).then(function(result) {
            propertyClass = result;
        });

        browser.close();

        return propertyClass;

    } catch (error) {
        console.log('MAIN ERR', error);
    }
};

