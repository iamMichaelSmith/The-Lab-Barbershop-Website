const { DateTime } = require("luxon");

module.exports = function (eleventyConfig) {
    // Passthrough copy (keep images/static files only; CSS is compiled)
    eleventyConfig.addPassthroughCopy({ "src/assets/images": "assets/images" });
    eleventyConfig.addPassthroughCopy({ "src/assets/js": "assets/js" });
    eleventyConfig.addPassthroughCopy("src/robots.txt");

    // Date filter
    eleventyConfig.addFilter("postDate", (dateObj) => {
        return DateTime.fromJSDate(dateObj).toLocaleString(DateTime.DATE_MED);
    });

    // Limit selection filter
    eleventyConfig.addFilter("limit", (arr, limit) => {
        return arr.slice(0, limit);
    });

    // Blog collection
    eleventyConfig.addCollection("blogs", function (collectionApi) {
        return collectionApi.getFilteredByGlob("src/blogs/*.md");
    });

    return {
        dir: {
            input: "src",
            output: "_site"
        }
    };
};
