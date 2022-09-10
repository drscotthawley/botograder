
def test_func(func_name):
    "returns True/False 1/0 if test passes/fails"
    try:
        print(f"  --- Running test of {func_name.__name__[5:]}():")
        func_name()
        print("      Passed.")
        return 1
    except:
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb) # Fixed format
        tb_info = traceback.extract_tb(tb)
        filename, line, func, text = tb_info[-1]

        print(f'An error occurred when running {func_name} in statement: {text}')
        return 0




#  some tests 

x2 = torch.tensor([[1,2,3],[4,5,6]])
print("x2 =\n",x2)
x2 = x2.float() # actually let's make it floats instead of ints
print("x2 =\n",x2)
batch_size, in_dim = x2.shape[0], x2.shape[1]; 
print(f"batch_size = {batch_size}, in_dim = {in_dim}")

torch.manual_seed(0)
mynet2 = MyNet( in_dim, 10, 10, 1 )

p2 = mynet2.forward(x2).detach().numpy()
print(p2)

tol = 1e-6   # some tolerable level of precision
target = np.array([[-0.13569488], [-0.18428665]])  # my answer (to some precision based on cut & paste!)


def test1():
    assert np.abs(p2 - target).sum() < tol, "Nope the difference is too great."

def check_preds(net, x, target, tol=1e-6):
    preds = net.forward(x).detach().numpy()
    assert np.abs(preds - target).sum() < tol, "Nope the difference is too great."
    print("Passed the test!")

def test2():
    torch.manual_seed(0)
    net = MyNet(x2.shape[1], 10,10, target.shape[1])
    check_preds(net, x2, target)

def test3():
    torch.manual_seed(0)
    x3 = torch.rand((3,4))   # a batch of 3 input vectors with 4 elements each
    net = MyNet(x3.shape[1], 30,30, 1)
    target = np.array([[-0.3079027 ],[-0.34663504],[-0.30993503]]) # what I got
    check_preds(net, x3, target)






func_list = [test1, test2, test3]
passed = 0
for func in func_list:
    passed += test_func(func)

print(f"\n{passed}/{len(func_list)} tests passed.")
