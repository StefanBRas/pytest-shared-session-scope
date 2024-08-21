# TODO
- [ ] make storage and cache type the same
- [ ] Make cleanup work
- [ ] do fancy stuff to inspect func and see if there's any clean up to do
- [ ] Maybe there's a way to make it more efficient, where we don't need the initial worker to do the cleanup, but can let any do it.
```python

@my_fixture:
def a():
  data: None | Data = yield # We send the data to the function OR None if it should compute
  if data is None:
    # calculate data
    ...
    data = 1
  yield data
  # Do clean up
```
