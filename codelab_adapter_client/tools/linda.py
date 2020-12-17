'''
codelab-linda --monitor
codelab-linda --out [1, "hello"]
codelab-linda --rd [1, "*"]
codelab-linda --in [1, "hello"]
codelab-linda --dump

todo
    json 输出，彩色

click
    adapter full 已经内置 click
'''
import time
import queue
import ast

import click
from codelab_adapter_client import AdapterNode
from codelab_adapter_client.topic import LINDA_SERVER, LINDA_CLIENT


class PythonLiteralOption(click.Option):
    def type_cast_value(self, ctx, value):
        try:
            return ast.literal_eval(value)
        except:
            raise click.BadParameter(value)


class CatchAllExceptions(click.Group):
    # https://stackoverflow.com/questions/44344940/python-click-subcommand-unified-error-handling
    def __call__(self, *args, **kwargs):
        try:
            return self.main(standalone_mode=False, *args, **kwargs)
        except Exception as e:
            click.echo(e)
        finally:

            mynode.terminate()  # ok!


class MyNode(AdapterNode):
    NODE_ID = "linda/linda_cli" # 是否有问题？

    def __init__(self, codelab_adapter_ip_address):  # todo 发给 Linda 的也订阅
        super().__init__(codelab_adapter_ip_address=codelab_adapter_ip_address)
        # self.set_subscriber_topic(LINDA_SERVER) # add topic
        self.set_subscriber_topic('')
        self.q = queue.Queue()


    def _linda_message_handle(self, topic, payload):
        # click.echo(f'{topic}, {payload}')
        self.q.put((topic, payload))
    
    '''
    def message_handle(self, topic, payload):
        if topic in [LINDA_SERVER, LINDA_CLIENT]:
            click.echo(f'{topic}, {payload}')
    '''

# tudo， help不要初始化，需要放到cli中，ctx传递到CatchAllExceptions



@click.group(cls=CatchAllExceptions)
@click.option('-i',
              '--ip',
              envvar='IP',
              help="IP Address of Adapter",
              default="127.0.0.1",
              required=False)
@click.pass_context
def cli(ctx, ip):
    '''
    talk with linda from cli
    '''
    # ctx.obj = mynode # todo ip ，多参数
    global mynode # 给退出时候用
    
    ctx.ensure_object(dict)
    mynode = MyNode(ip)
    mynode.receive_loop_as_thread()
    
    time.sleep(0.05)

    ctx.obj['node'] = mynode
    ctx.obj['ip'] = ip


@click.command()
@click.pass_obj
def dump(ctx):
    '''
    dump all tuples from Linda tuple space
    '''
    res = ctx['node'].linda_dump()
    click.echo(res)
    return ctx['node']


@cli.command()
@click.option('-d', '--data', cls=PythonLiteralOption, default=[])
@click.pass_obj
def out(ctx, data):
    '''
    out the tuple to Linda tuple space
    '''
    # codelab-linda out --data '[1, "hello"]'
    # codelab-linda --ip '192.168.31.111'  out --data '[1, "hello"]' # 注意参数位置！
    assert isinstance(data, list)
    click.echo(f'ip: {ctx["ip"]}')
    res = ctx['node'].linda_out(data)
    click.echo(res)
    return ctx['node']


@click.command("in")
@click.option('-d', '--data', cls=PythonLiteralOption, default=[])
@click.pass_obj
def in_(ctx, data):  # replace
    '''
    in the tuple to Linda tuple space
    '''
    # codelab-linda in --data '[1, "*"]'

    assert isinstance(data, list)
    res = ctx["node"].linda_in(data)
    click.echo(res)
    return ctx["node"]


@click.command()
@click.option('-d', '--data', cls=PythonLiteralOption, default=[])
@click.pass_obj
def inp(ctx, data):  # replace
    '''
    inp(in but Non-blocking) the tuple to Linda tuple space
    '''
    # codelab-linda inp --data '[1, "*"]'
    assert isinstance(data, list)
    res = ctx["node"].linda_inp(data)
    click.echo(res)
    return ctx["node"]


@click.command()
@click.pass_obj
def monitor(ctx):  # replace
    '''
    linda message monitor
    '''
    while ctx["node"]._running:
        if not ctx["node"].q.empty():
            click.echo(ctx["node"].q.get())
        time.sleep(1)


@cli.resultcallback()
def process_result(result, **kwargs):
    # click.echo(f'After command: {result} {kwargs}')
    # result is node
    if result and result._running:
        result.terminate()


cli.add_command(dump)
cli.add_command(out)
cli.add_command(in_)
cli.add_command(inp)
cli.add_command(monitor)