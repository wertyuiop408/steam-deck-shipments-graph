## Readme

Script to show the current rate of shipments by Valve for the steam deck and outputting to a graph.

To add models/regions, use the `graph_query` method and add it around Ln #103, 
```
uk_512_x, uk_512_y = self.graph_query("UK", 512)
ax.scatter(uk_512_x, uk_512_y, 10, label="UK-512")
```

![](graph.png)


## Install

```
py -m venv env --upgrade-deps
.\env\Scripts\activate
pip install -r requirements
```

## Usage

```
py main.py --upgrade
```
