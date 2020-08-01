# ``sidewalk_gaps.extract_data``

This module exists to clip out data from the ``public`` schema into a new schema for a specific analysis.

## CLI Usage

Specify the following:
- database with ``-d`` or ``--database`` 
- municipality name with ``-m`` or ``--municipality`` (defaults to none)
- buffer distance with ``-b`` or ``--buffer`` (defaults to zero)

You must also specify the state as the final argument. Use ``nj`` or ``pa``

```
sidewalk clip-data -d gap_analysis nj
```