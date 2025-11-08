import pandas as pd

# df = pd.read_csv("C:\\Users\\Muhammed nasr fayez\\Downloads\\username.csv")
# print(df.shape)


file_id = '18Aie7PXX77qZj1mFHp2YXw-gzBstu19p'
url = f"https://drive.google.com/uc?export=download&id={file_id}"


# data = pd.read_csv(url)
# print(data.head())
# print(data.info())

# print(pd.__version__)


list1 = [1, "ahmed" , 52.8]
pdlist = pd.Series(list1 , ["value1", "value2", "value3"])
print(pdlist)
print(pdlist.shape())