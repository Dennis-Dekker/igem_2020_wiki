#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple Script to upload multiple HTML, CSS or JS files to the iGEM Wiki.

Copyright under MIT License, see LICENSE.
"""
from __future__ import print_function
from igem_manager import BaseIGemWikiManager
import os
import sys

if sys.version_info[0] < 3:
    from urlparse import urlparse, urlunparse
else:
    from urllib.parse import urlparse, urlunparse

__author__ = "Joeri Jongbloets <joeri@jongbloets.net>"


class IGemFile(object):

    IMAGE_EXTENSIONS = ('jpg', 'jpeg', 'png', 'bmp', 'gif')

    def __init__(self, path, destination=None, prefix=None, mime=None, **kwargs):
        self._path = path
        self._destination = destination
        self._prefix = prefix
        self._url = None
        self._mime = mime
        self._arguments = kwargs

    @property
    def path(self):
        return self._path

    @property
    def prefix(self):
        return self._prefix

    @property
    def full_path(self):
        return os.path.join(self.prefix, self.path)

    @property
    def extension(self):
        extension = os.path.splitext(self.path)[1]
        return extension.strip(".")

    @property
    def destination(self):
        return self._destination

    @destination.setter
    def destination(self, d):
        self._destination = d

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, u):
        self._url = u

    @property
    def mime(self):
        return self._mime

    @mime.setter
    def mime(self, m):
        self._mime = m

    def exists(self):
        return os.path.exists(self.path)

    def is_html(self):
        return self.extension == "html"

    def is_stylesheet(self):
        return self.extension == "css"

    def is_javascript(self):
        return self.extension == "js"

    def is_image(self):
        return self.extension in self.IMAGE_EXTENSIONS

    def is_resource(self):
        return self.extension not in ("html", "css", "js")

    def __str__(self):
        return "{} => {}".format(self.path, self.destination)


class IGemUploader(BaseIGemWikiManager):

    def __init__(self, team=None, year=None):
        super(IGemUploader, self).__init__(team=team, year=year)
        self._files_collected = []
        self._files_uploaded = []
        self._strip_paths = False

    @property
    def collected_files(self):
        """List of all files collected from the given patterns

        :rtype: list[IGemFile]
        """
        return self._files_collected

    @property
    def uploaded_files(self):
        """List of all files uploaded to the wiki

        :rtype: list[IGemFile]
        """
        return self._files_uploaded

    def do_strip(self):
        return self._strip_paths is True

    def set_strip(self, state):
        self._strip_paths = state is True

    def execute(self, action):
        # collect files
        self.collect_patterns(self._files)
        if action == "upload":
            if self.login():
                uploads = self.upload_files()
                self.get_logger().info("Uploaded {} files".format(uploads))

    def collect_patterns(self, patterns):
        results = []
        for pattern in patterns:
            result = self.collect_pattern(pattern)
            results.extend(result)
            self.get_logger().debug("Collected {} files matching pattern {}".format(
                    len(result), pattern
                )
            )
        # do post processing ?!
        self._files_collected = results
        self.get_logger().debug("Collected {} files in total".format(
                len(results)
            )
        )
        return results

    def collect_pattern(self, pattern, base=None):
        import glob
        results = []
        if self.do_strip() and base is None:
            base = os.path.dirname(pattern)
        for source in glob.glob(pattern):
            if os.path.exists(source):
                if os.path.isdir(source):
                    # take all files from the directory
                    results.extend(self.collect_pattern(os.path.join(source, "*"), base=base))
                if os.path.isfile(source):
                    result = self.collect_file(source, base=base)
                    # TODO: Duplicate destination check?!
                    results.append(result)
        # squash files
        return results

    def collect_file(self, source, base=None):
        destination = None
        if base is not None:
            # remove pattern from the file name
            destination = source.replace(base, "", 1)
        return IGemFile(source, destination=destination, prefix=base)

    def upload_files(self):
        results = 0
        # collected files is a list of IGemFile objects
        files = self.collected_files
        # first we upload resources so we can update their destinations
        resources = filter(lambda f: f.is_resource(), files)
        print("## Uploading {} resources".format(len(resources)))
        for resource in resources:
            results += 1 if self.upload_resource(resource) else 0
        # upload all stylesheets
        resources = filter(lambda f: f.is_stylesheet(), files)
        print("## Uploading {} stylesheets".format(len(resources)))
        for resource in resources:
            results += 1 if self.upload_stylesheet(resource) else 0
        resources = filter(lambda f: f.is_javascript(), files)
        print("## Uploading {} javascripts".format(len(resources)))
        for resource in resources:
            results += 1 if self.upload_stylesheet(resource) else 0
        # upload all html
        resources = filter(lambda f: f.is_html(), files)
        print("## Uploading {} html files".format(len(resources)))
        for resource in resources:
            results += 1 if self.upload_html(resource) else 0
        return results

    def upload_file(self, f, content=None):
        """Core function acts as interface between edit and the upload methods

        :type f: IGemFile
        """
        result = False
        if f.is_resource():
            # upload using the upload method
            if f.exists():
                result = self.upload(f.destination, f.path)
                url = result.get("url")
                mime = result.get("mime")
                if url is not None:
                    f.url = url
                if mime is not None:
                    f.mime = mime
        else:
            if content is None and f.exists():
                with open(f.path, "rb") as src:
                    content = "".join(src.readlines())
            if content is not None:
                result = self.edit(f.destination, content)
                self.get_logger().debug("Uploaded {}: {}".format(f, result))
                f.url = self.prefix_url(f.destination)
        if result:
            self.collected_files.remove(f)
            self.uploaded_files.append(f)
        return result

    def upload_html(self, f):
        """Upload HTML files

        :type f: IGemFile
        """
        result = False
        # remove any .html extension from the file
        if f.destination is None:
            f.destination = f.path
        name = f.destination
        name = name.lstrip("./")
        if name.endswith(".html"):
            name = name.replace(".html", "")
        f.destination = self.prefix_title(name)
        if f.exists():
            # obtain content
            with open(f.path, "rb") as src:
                content = "".join(src.readlines())
            # process content
            content = self.prepare_html(content)
            self.upload_file(f, content)
        return result

    def upload_stylesheet(self, f):
        """Upload a CSS Stylesheet

         :type f: IGemFile
        """
        result = False
        if f.destination is None:
            f.destination = f.path
        name = f.destination
        name = name.lstrip("./")
        if name.endswith(".css"):
            name = name.replace(".css", "")
        f.destination = self.prefix_title(name)
        if f.exists():
            # obtain content
            with open(f.path, "rb") as src:
                content = "".join(src.readlines())
            # process content
            content = self.prepare_stylesheet(content)
            self.upload_file(f, content)
        return result

    def upload_javascript(self, f):
        """Upload a CSS Stylesheet

         :type f: IGemFile
        """
        result = False
        if f.destination is None:
            f.destination = f.path
        name = f.destination
        name = name.lstrip("./")
        if name.endswith(".css"):
            name = name.replace(".css", "")
        f.destination = self.prefix_title(name)
        if f.exists():
            # obtain content
            with open(f.path, "rb") as src:
                content = "".join(src.readlines())
            # process content
            content = self.prepare_javascript(content)
            self.upload_file(f, content)
        return result

    def upload_resource(self, f):
        """Upload resources like Images, PDFs etc."""
        result = False
        if f.destination is None:
            f.destination = f.path
        name = f.destination
        name = name.lstrip("./")
        name = self.prefix_title(name)
        f.destination = self.prefix_title(name)
        if f.exists():
            self.get_logger().info("Upload attachment {}".format(f))
            result = self.upload_file(f)
        return result

    def prepare_html(self, html):
        from bs4 import BeautifulSoup
        doc = BeautifulSoup(html, "html.parser")
        # fix all stylesheet imports
        elements = doc.find_all("link", rel="stylesheet")
        for e in elements:
            href = e.get("href")
            if href is not None:
                uri = self.fix_stylesheet_link(href)
                self.get_logger().debug("Changed stylesheet href {} to {}".format(href, uri))
                e["href"] = uri
        elements = doc.find_all("script")
        # fix all javascript imports
        for e in elements:
            src = e.get("src")
            if src is not None:
                uri = self.fix_javascript_source(src)
                self.get_logger().debug("Changed script src {} to {}".format(src, uri))
                e["src"] = uri
        # fix all links
        elements = doc.find_all("a")
        for e in elements:
            href = e.get("href")
            if href is not None:
                uri = self.fix_html_link(href)
                self.get_logger().debug("Changed link href {} to {}".format(href, uri))
                e["href"] = uri
        # fix all image links
        elements = doc.find_all("img")
        for e in elements:
            src = e.get("src")
            if src is not None:
                uri = self.fix_image_link(src)
                self.get_logger().debug("Changed img src {} to {}".format(src, uri))
                e["src"] = uri
        # write to string
        result = doc.prettify()
        return result

    def prepare_stylesheet(self, stylesheet):
        """Inspect a stylesheet on URL's we should change"""
        result = stylesheet
        return result

    def prepare_javascript(self, script):
        """Inspect a JavaScript on URL's we should change"""
        result = script
        return result

    def fix_stylesheet_link(self, href):
        match = self.find_actual_link(href)
        if match is not None:
            uri = match.url
        else:
            uri = href.rsplit(".", 1)[0]
            uri = self.prefix_url(uri)
        if not uri.endswith("?action=raw&ctype=text/css"):
            uri += "?action=raw&ctype=text/css"
        return uri

    def fix_javascript_source(self, src):
        match = self.find_actual_link(src)
        if match is not None:
            uri = match.url
        else:
            uri = src.rsplit(".", 1)[0]
            uri = self.prefix_url(uri)
        if not uri.endswith("?action=raw&ctype=text/js"):
            uri += "?action=raw&ctype=text/javascript"
        return uri

    def fix_image_link(self, src):
        url = src
        # we need to be careful, images can be both internal and external!
        # take url apart
        parts = list(urlparse(src))
        # get base url
        base_url = self.get_base_url()
        base_url = base_url.replace("https://", "")
        base_url = base_url.replace("http://", "")
        # extract local path
        path = str(parts[2])  # .strip("/")
        # check if this is a local file
        if path != "" and parts[1] in ("", base_url):
            ctype = "&ctype=text/plain"
            mime = None
            url = self.prefix_url(url)
            match = self.find_actual_link(src)
            if isinstance(match, IGemFile):
                mime = match.mime
                url = match.url
                if url is None:
                    url = self.prefix_url(match.destination)
            if mime is None:
                mime = os.path.splitext(url)[1]
            if isinstance(mime, str):
                mime = mime.strip(".")
            if mime in IGemFile.IMAGE_EXTENSIONS:
                ctype = "&ctype=image/{}".format(mime)
            # if not url.endswith("?action=raw{}".format(ctype)):
            #     url += "?action=raw{}".format(ctype)
        else:
            url = self.fix_html_link(src)
        return url

    def fix_html_link(self, href):
        url = href
        # we have to be careful, we only want to change the uri not any params or internal links
        parts = list(urlparse(href))
        # get a clean base url
        base_url = self.get_base_url()
        base_url = base_url.replace("https://", "")
        base_url = base_url.replace("http://", "")
        # extract local path
        path = str(parts[2]) #.strip("/")
        if path != "" and parts[1] in ("", base_url):
            target = ""
            pieces = path.rsplit("#", 1)
            path = pieces[0]
            if len(pieces) > 1:
                target = pieces[-1]
            target = target.strip("/")
            path = path.rsplit(".", 1)[0]
            if path == "/":
                path = "index"
            # we will set the parts["netloc"] to the right server
            # so we do not worry about that part
            path = self.prefix_title(path)
            # reassemble
            parts[0] = "http"
            parts[1] = base_url
            parts[2] = path + target
            url = urlunparse(parts)
        return url

    def find_actual_link(self, fn):
        """Searches through the uploaded files list to get the actual link of the files

        This can be a link or an source but will always return the actual destination
        """
        url = self.prefix_title(fn)
        result = None

        def is_match(f):
            matches_names = fn in (f.destination, f.path, f.full_path, f.url)
            matches_paths = fn.strip("./") in (
                f.destination.strip("./"), f.path.strip("./"), f.full_path.strip("./"), f.url.strip("./")
            )
            matches_url = url in (f.destination, f.url)
            return matches_names or matches_paths or matches_url

        matches = filter(is_match, self.uploaded_files)
        if len(matches) > 0:
            self.get_logger().debug("Matched {} to:\n{}".format(fn, [str(m) for m in matches]))
            match = matches[0]
            result = match
        return result



    @classmethod
    def create_parser(cls, parser=None):
        parser = super(IGemUploader, cls).create_parser(parser)
        parser.description = "Simple file upload script for the iGEM wiki"
        parser.add_argument(
            '--strip', action="store_true", help="Remove pattern from filename", default=None
        )
        return parser

    def parse_arguments(self, arguments):
        super(IGemUploader, self).parse_arguments(arguments)
        do_strip = arguments.get("strip")
        if do_strip is not None:
            self.set_strip(self.parse_bool(do_strip))


if __name__ == "__main__":
    IGemUploader.run()
