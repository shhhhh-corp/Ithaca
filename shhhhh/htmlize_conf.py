import sys

import yaml
from json2html import json2html


def main(conf_path):
    # Templating is so 2020
    html = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>Your OX configuration</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/tufte-css/1.8.0/tufte.min.css" integrity="sha512-F5lKjC1GKbwLFXdThwMWx8yF8TX/WVrdhWYN9PWb6eb5hIRLmO463nrpqLnEUHxy2EHIzfC4dq/mncHD6ndR+g==" crossorigin="anonymous" referrerpolicy="no-referrer"></link>
        <style type="text/css">
         td,
         th {
             border: 1px solid rgb(190, 190, 190);
             padding: 10px;
         }

         td {
             text-align: center;
         }

         tr:nth-child(even) {
             background-color: #eee;
         }

         tr:nth-child(odd) {
             background-color: #fffff8;;
         }

         th[scope="col"] {
             background-color: #696969;
             color: #fff;
         }

         th[scope="row"] {
             background-color: #d7d9f2;
         }

         caption {
             padding: 10px;
             caption-side: bottom;
         }

         table {
             border-collapse: collapse;
             border: 2px solid rgb(200, 200, 200);
             letter-spacing: 1px;
             font-family: sans-serif;
             font-size: .8rem;
         }
        </style>
    </head>
    <body>
        <h1>Your OX configuration</h1>
        <div>
    """

    with open(conf_path) as f:
        conf = yaml.safe_load(f)
        html += json2html.convert(json=conf, table_attributes='border="1" class="sans"')

    html += """
        </div>
    </body>
</html>
    """

    with open("./configuration.html", "w") as out:
        out.write(html)

    print('configuration formatted to html in "./configuration.html"')


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "./conf.yaml")
