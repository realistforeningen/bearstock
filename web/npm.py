from webassets.filter import Filter

class NodebugFilter(Filter):
    name = 'nodebug'
    max_debug_level = None

    def input(self, _in, out, **kwargs):
        out.write(_in.read())

class ImbaCompileFilter(Filter):
    name = 'imba'
    max_debug_level = None

    def setup(self):
        import execjs
        self.ctx = execjs.get('Node').compile("""
            module.paths.push(process.cwd() + "/node_modules");

            var Imbac = require("imba/compiler");

            function compile(txt) {
                return Imbac.compile(txt).toString();
            }
        """)

    def input(self, _in, out, **kwargs):
        out.write(self.ctx.call('compile', _in.read()))

_resolver = None

def resolve(path):
    global _resolver
    if _resolver is None:
        import execjs
        _resolver = execjs.get('Node').compile("""
            module.paths.push(process.cwd() + "/node_modules");

            function resolve(str) {
                return require.resolve(str);
            }
        """)

    return _resolver.call('resolve', path)


def register():
    from webassets.filter import register_filter
    register_filter(ImbaCompileFilter)
    register_filter(NodebugFilter)

