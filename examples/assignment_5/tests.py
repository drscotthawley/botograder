# Example instructor-supplied tests: test1(), test2(), test3() 
# Each takes no arguments, each one contains an assert.

tol = 1e-6   # some tolerable level of precision

# defining this here so we can use it in the_generator(), below. Leave this cell alone
class AddChannels(Module):
    "utility layer: this just does the 'unsqueeze_noise' inside a PyTorch module"
    def __init__(self, n_dim):  # note fastai will expect n_dim to be an arg, not a kwarg
        self.n_dim = n_dim
    def forward(self, x):
        return unsqueeze_noise(x, n_dim=self.n_dim)

def calc_big(small, stride=2, kernel_size=4, padding=1): # sizing of transposed convolution output
    return (small-1)*stride + kernel_size - 2*padding

def calc_small(big, stride=2, kernel_size=4, padding=1): # sizing of regular convolution output, as per eq1.
     return  (big + 2*padding - kernel_size) // stride + 1

# Student-facing tests for generator_block
test_batch_size, z_dim = 83, 121


def test1():
    noise = get_noise(1247, 34763)  # just some arbitrary dimensions
    assert noise.mean().abs() < 1e-3, f"noise.mean() should be close to zero but it's {noise.mean()}"
    assert (noise.var() - 1).abs() < 1e-3, f"noise.var() should be close to one but it's {noise.var()}"
    print("Success!")

def compare_shapes(a_tensor, shape_as_list):
    "since lots of our tests are going to be comparing shapes, I just wrote this little utility"
    assert list(a_tensor.shape) == shape_as_list, f"{list(a_tensor.shape)} != {shape_as_list}"

def test2():
    noise = get_noise(1247, 34763)  # just some arbitrary dimensions
    unsq_noise = unsqueeze_noise(noise)
    print("unsq_noise.shape = ",unsq_noise.shape)
    compare_shapes(unsq_noise, list(noise.shape)+[1]*2)
    compare_shapes(unsqueeze_noise(torch.randn(345,678), n_dim=4), [345,678,1,1,1,1])
    print("Success!")

def check_preds(net, x, target, tol=1e-6):
    preds = net.forward(x).detach().numpy()
    assert np.abs(preds - target).sum() < tol, "Nope the difference is too great."
    print("Passed the test!")

def test3():
    torch.manual_seed(0)
    # Student-facing tests for generator_block
    test_batch_size, z_dim = 83, 121
    
    gb1 = generator_block(z_dim, 13)
    assert len(gb1) == 3, "should have exactly 3 layers"
    in1 = unsqueeze_noise( get_noise(test_batch_size, z_dim) )
    out1 = gb1(in1)
    compare_shapes(out1, [test_batch_size, 13, 2, 2])
    assert isinstance(gb1[-1], nn.ReLU), 'activation should be ReLU'
    
    gb2 = generator_block(256, 512, kernel_size=2)
    in2 = torch.rand(test_batch_size, 256, 28, 28)
    out2 = gb2(in2)
    compare_shapes(out2, [test_batch_size, 512, 54, 54])
    
    gb3 = generator_block(256, 512, kernel_size=2, padding=0, stride=1, final_block=True)
    assert len(gb3) == 2, "final block should have exactly 2 layers"
    in3 = torch.rand(test_batch_size, 256, 28, 28)
    out3 = gb3(in3)
    compare_shapes(out3, [test_batch_size, 512, 29, 29])
    assert isinstance(gb3[-1], nn.Tanh), 'activation should be Tanh'
    print("Success!")




def test4():
    torch.manual_seed(0)
    # Student-facing testing code for the_generator() 
    
    def show_ct_shapes(net, small=1, log=True):
        """Utility: Shows changes to 'internal' image shapes in a model, due to ConvTranspose2d's' """
        if log: print("ConvTranspose2d transformations of 'image' shapes:")
        out_shapes = []  # list of shapes of the 'output' of each convtranspose2d
        for block in net.children():
            if isinstance(block, nn.Sequential): 
                for l in block.children():
                    if isinstance(l, nn.ConvTranspose2d):
                        ic, oc = l.in_channels, l.out_channels
                        k,s,p = l.kernel_size[0], l.stride[0], l.padding[0]
                        big = calc_big(small, kernel_size=k, stride=s, padding=p)
                        if log: print(f"({ic},{small},{small}) -> ({oc},{big},{big})")
                        out_shapes.append((oc,big,big))
                        small = big
        return out_shapes 
    
    gen = the_generator()
    shapes= show_ct_shapes(gen)
    print("shapes = ",shapes)
    # make sure these are as expected
    assert shapes == [(512, 2, 2), (256, 4, 4), (128, 8, 8), (64, 16, 16), (64, 32, 32), (3, 64, 64)]
    print("Success!")


def test5():
    # Student-facing tests for discriminator_block
    
    db1 = discriminator_block(256, 13)
    assert len(db1) == 3, "should have exactly 3 layers"
    in1 = torch.rand(test_batch_size, 256, 64, 64) 
    out1 = db1(in1)
    compare_shapes(out1, [test_batch_size, 13, 32, 32])
    assert isinstance(db1[-1], nn.LeakyReLU), 'activation should be LeakyReLU'
    
    db2 = discriminator_block(256, 512, kernel_size=3, stride=2, padding=2)
    in2 = in1
    out2 = db2(in2)
    compare_shapes(out2, [test_batch_size, 512, 33, 33])
    
    db3 = discriminator_block(128, 57, kernel_size=3, padding=0, stride=1, final_block=True)
    assert len(db3) == 1, "final block should have exactly 1 layer"
    in3 = torch.rand(test_batch_size, 128, 28, 28)
    out3 = db3(in3)
    compare_shapes(out3, [test_batch_size, 57, 26, 26])
    assert isinstance(db3[-1], nn.Conv2d), 'final layer should be Conv2d'
    print("Success!")


def test6():
        # Student-facing testing code for the_discriminator()
    
    
    def show_conv2d_shapes(net, big=64, log=True):
        """Utility: Shows changes to 'internal' image shapes in a model, due to Conv2d's' """
        if log: print("Conv2d transformations of 'image' shapes:")
        out_shapes = []  # list of shapes of the 'output' of each convtranspose2d
        for block in net.children():
            if isinstance(block, nn.Sequential):
                for l in block.children():
                    if isinstance(l, nn.Conv2d):
                        ic, oc = l.in_channels, l.out_channels
                        k,s,p = l.kernel_size[0], l.stride[0], l.padding[0]
                        small = calc_small(big, kernel_size=k, stride=s, padding=p)
                        if log: print(f"({ic},{big},{big}) -> ({oc},{small},{small})")
                        out_shapes.append((oc,small,small))
                        big = small
        return out_shapes
    
    disc = the_discriminator()
    shapes= show_conv2d_shapes(disc)
    print("shapes = ",shapes)
    # make sure these are as expected
    assert shapes == [(64, 32, 32), (64, 16, 16), (128, 8, 8), (256, 4, 4), (512, 2, 2), (1, 1, 1)]
    print("Success!")



def test_func(func_name):
    """
    Generic function tester: returns True/False 1/0 if test passes/fails. 
    Passes = executes w/o error, e.g. w/o failed asserts
    """
    try:
        print(f"  \n--- Running test of {func_name.__name__}():")
        func_name()
        print("      Passed.")
        return 1
    except Exception as e:
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb) # Fixed format
        tb_info = traceback.extract_tb(tb)
        filename, line, func, text = tb_info[-1]

        print(f'An error occurred when running {func_name} in statement: {text}')
        print(f'   Exception = {e}')
        return 0




func_list = [test1, test2, test3, test4, test5, test6]  # 
passed = 0
for func in func_list:
    passed += test_func(func)  # TODO: maybe not best to have to supply test_func for each assignment

print(f"\n{passed}/{len(func_list)} tests passed.")
