def check_preds(net, x, target, tol=1e-6):
    preds = net.forward(x).detach().numpy()
    assert np.abs(preds - target).sum() < tol, "Nope the difference is too great."
    print("Passed the test!")

torch.manual_seed(0)
net = MyNet(x2.shape[1], 10,10, target.shape[1])
check_preds(net, x2, target)

torch.manual_seed(0)
x3 = torch.rand((3,4))   # a batch of 3 input vectors with 4 elements each
net = MyNet(x3.shape[1], 30,30, 1)
target = np.array([[-0.3079027 ],[-0.34663504],[-0.30993503]]) # what I got
check_preds(net, x3, target)

