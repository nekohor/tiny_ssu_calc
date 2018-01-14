# Tiny Shape clacs!


## 依赖
本程序严重依赖python-pandas。并且过程参数按照DataFrame的逻辑组织。

## 约定大于配置（CoC）

约定，在七个机架一起考虑的情况下，七机架所在DataFrame的索引，用数字1到7表示，而不使用默认的0到6。
那么在新建DataFrame时，需要预设index:
```python
index=np.array([1,2,3,4,5,6,7])
```