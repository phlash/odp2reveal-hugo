# odp2reveal-hugo
Open Document Presentation to Reveal.js (hosted by Gohugo) conversion script

## Inspiration
The Awesome (sic) [AwesomeSlides](https://github.com/cliffe/AwesomeSlides) script, thanks Cliffe :)

## Target system
I use [Hugo](https://GoHugo.io) to build my personal website, and wanted a web-based slide tech that
fitted in, and allowed me to port existing ODP presentations. It took a few hours of experimenting
to discover the right approach: I started with Viewer.JS, which looked promising but only displayed
the footer text and meant managing binary files in git.. not appealing; moving on to slide tech that
used textual inputs, it looked like Reveal.js was the leader of the pack, and usefully had support
directly in hugo courtesy of [Reveal-hugo](https://github.com/dzello/reveal-hugo), thanks Josh!

## The need
So after much fiddling with Hugo on [my website](https://github.com/phlash/www.ashbysoft.com) I had
a working demo of a basic slide pack, both full screen and embedded in a blog post - neat. Just the
task of converting ODP files now.. step forward AwesomeSlides, except it targets raw Reveal.js in
HTML, not Hugo in Markdown, and has a few Perl dependencies, could I do similar in self-contained
Python? Well, it works for me :)

## Usage
`odp2reveal-hugo.py <input ODP> -o <output folder>` will hopefully spit out a <input base>.md and
copies of any referenced images in the ODP document. The output markdown file should be directly
usable as `'index.md` in reveal-hugo (thus index.md plus images is a page bundle).

Tack on `-h` to get command line syntax, `-v` for verbosity (two levels, repeat `-v`) and override
the default front matter `-t <title>` and `-s <summary>` text if you wish.

## Feedback
Issues and pull requests welcome!
