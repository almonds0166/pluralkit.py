
# Building the docs

1. In a terminal/prompt, navigate to this folder (`.../docs/`).

2. Make sure to have the requirements installed in your environment. (Also install the main project's requirements of course, if one has not already done so.)

   ```bash
   pip install -r requirements.txt
   ```

3. Clean the build directory (if there was ever anything in there to begin with).

   ```bash
   sphinx-build -M clean source/ build/
   ```

4. Touch up the reST files under `source/`.

5. Make the docs.

   ```bash
   sphinx-build -M html source/ build/
   ```

   The output under `.../docs/build/html/` represents the HTML documentation.