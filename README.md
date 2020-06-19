# iGEM Wiki Template using Bootstrapped Middleman

This templates combines several tools for fast website development targeted to the iGEM wiki environment.

Tools included:

- Middleman (v4): For automatic static web page generation
- Bootstrap (v4.0-beta): CSS Framework to ease web design
- uploader script: For fast and easy page upload

Features:

- CSS Normalizer stylesheet to remove unwanted effects from the iGEM CSS Environment
- Local preview (including iGEM CSS environment)
- Upload fixes links to stylesheets and scripts (adding `&action=raw&ctype=text/<mime-type>`)

## Requirements

* Ruby and RubyGems
* Python (2.7 tested, 3 and above should work)
* Python packages: requests and beautifulsoup4
* XCode (macOS)

## Usage

1. Download (git clone) the repository.
2. In Terminal run `gem install bundler`
3. Move into the repository folder (e.g. `cd igem_template`)
4. Run `bundle install` (installs all ruby dependencies)
5. Run `pip install requests beautifulsoup4`

To build the site:

- `middleman build` (or `bundle exec middleman build`)

To preview the site:

- `middleman server` (or `bundle exec middleman server`)

To upload the site (after building):

1. Create an ini file (`igem.ini` for example):

```ini
username: <igem username>
password: <igem password>
team: <igem team name>
strip: 1
# in case you want to upload to a specific location
# Example: 'Team:Name/index` => 'Team:Name/prefix/index'
# Uncomment the following:
#prefix: prefix
``` 

2. Run the upload script:

`igem_upload.py --ini igem.ini upload "./build/*`"

This will upload all files in the build directory to the iGEM Wiki.

NOTE: The quotes around the file pattern may be necessary to prevent the terminal from expanding it before passing it
 to Python.

## CSS Reset

There are multiple strategies possible if one wants to reset CSS Styles for a particular part of a website. Normally 
one could reset the styles of all the elements of the document, assuming there is no other stylesheet that may 
interfere. In order to understand how stylesheet interfere, you must understand how CSS determines which style rules 
are applied and which are ignored. This mechanism is called "specificity" ([1]) and it will determine the order in 
which 
styles are to be applied. In short; element-style (defined using the `style=`) are most important, then come rules 
defined that include an ID, then rules with classes and last rules that specify elements.

```
#id { font-size: 14}    => (1, 0, 0)
.class { font-size: 15 } => (0, 1, 0)
p { font-size: 16 } => (0, 0, 1)
``` 

Unfortunately the iGEM wiki designers decided to settle on ID's making their rules highly specific (we can only 
trump it by using ID's too). This is particularly a problem in the case of this rule, which is designed to reset the 
style of the paragraph attribute, however since it is so specific overloading it is fairly difficult (and certainly 
not done by many template by default).

```css
#HQ_page p {
	font-family: "Arial", Helvetica, sans-serif;
	font-size: 13px;
	text-align: justify
}
```

To solve this one can do two things:

1. Adjust your template to be more specific than any of the iGEM styles.
2. Redefine the iGEM rules.

Both have benefits and disadvantages, to name a few:

The first strategy can be implemented using SASS or SCSS (which we do, look at the assets!) by nesting template 
imports in a very specific rule (`#bodyContent`). However, this will break certain rules, such as rules specifying 
the body or html tags (imagine: `#bodyContent html`, it will never exist!) We'll need to redefine those rules 
separately. 

The second strategy can be implemented by just declaring the same rule as the one we want to alter and reset it's 
style. This can be a powerful and useful tool (it is used in the case of `#HQ_page p`):

```css
#HQ_page,
#HQ_page p,
#HQ_page a {
    font-family: inherit;
    font-size: 1rem;
    text-align: inherit;
    color: inherit;
}
```

NOTE: the use of inherit assumes you have defined another style that is less specific (or targets the parent element), 
which should be applied instead.

TLDR; In the template, CSS Styles are reset using two techniques. By using both techniques a thorough reset was 
achieved, however keep in mind that these techniques depend on the template used.

## TODO's

- Implement configuration of "no index"; i.e. index files are named after the folder they are in.
- Implement accelerated mode for uploader (only new/changed and/or disabled uploads of certain file types)

[1]: https://developer.mozilla.org/en-US/docs/Web/CSS/Specificity
