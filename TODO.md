# Roadmap

### MS-4 - v0.1.2

- [x] ✍️ add `py.typed` to package
- [x] 📖 add patch notes
- [ ] ✍️ use github workflows:
  - [x] pytest on all py versions
  - [x] use cache for pip
  - [ ] automate publishing
- [ ] 📖 add tests status to repo page
- [ ] ⭐ publish `v0.1.2` 


## History

### MS-1 - pypi

- [x] 📖 write detailed description with code examples
- [x] ⭐ push this repo to `github`
- [x] ⭐ push package to pypi (create tokens and etc., research it!)

### MS-2 - v0.1.0

- [x] ✍️ **NO** include all `typer` declarations to `typer_di` (like in examples above)
- [x] ✍️ support *future* `annotations`
- [x] ✍️ fix tests up to py3.7
- [x] 📖 specify supported python versions
- [x] 🐞 **NO** dependency can be called multiple times in `callback` and `command`: we need to cache such calls through whole program execution
- [x] 📖 add patch notes
- [x] ⭐ publish `v0.1.0` 


### MS-3 - v0.1.1

- [x] 🐞 invalid duplicated names validation
- [x] ✍️ add checks for loops in dependencies
- [x] 📖 add patch notes
- [x] ⭐ publish `v0.1.1` 
