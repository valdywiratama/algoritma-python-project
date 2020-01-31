from flask import Flask, render_template
# flask = module kita, Flask = kelas yang ingin kita buat objectnya.
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# how to render matplotlip untuk disimpan ke server dengan disave .png, jadi dia butuh dirender orang
from io import BytesIO
import base64

app = Flask(__name__)

# bacalah file `googleplaystore.csv` data dan simpan ke objek dataframe dengan nama playstore
playstore = pd.read_csv("data/googleplaystore.csv")
# Hapus data yang duplikat berdasarkan kolom App, dengan tetap mempertahankan data pertama
playstore.drop_duplicates(subset='App', keep="first", inplace=True)
# bagian ini untuk menghapus row 10472 karena nilai data tersebut tidak tersimpan pada kolom yang benar
playstore.drop([10472], inplace=True)
# Cek tipe data kolom Category. Jika masih tersimpan dengan format tipe data yang salah, ubah ke tipe data yang sesuai
playstore['Category'] = playstore['Category'].astype('category')
# Pada kolom Installs Buang tanda koma(,) dan tanda tambah(+) kemudian ubah tipe data menjadi integer
playstore['Installs'] = playstore['Installs'].apply(lambda x: x.replace(',', ''))
playstore['Installs'] = playstore['Installs'].apply(lambda x: x.replace('+', ''))
# ubah jadi integer
playstore['Installs'] = playstore['Installs'].astype(int)

playstore['Size'].replace('Varies with device', np.nan, inplace = True ) 
playstore.Size = (playstore.Size.replace(r'[kM]+$', '', regex=True).astype(float) * \
             playstore.Size.str.extract(r'[\d\.]+([KM]+)', expand=False)
            .fillna(1)
            .replace(['k','M'], [10**3, 10**6]).astype(int))
playstore['Size'].fillna(playstore.groupby('Category')['Size'].transform('mean'),inplace = True)

# Pada kolom Price, buang karakater $ pada nilai Price lalu ubah tipe datanya menjadi float
playstore['Price'] = playstore['Price'].apply(lambda x: x.replace('$', ''))
# Float
playstore['Price'] = playstore['Price'].astype(float)
# Ubah tipe data Reviews, Size, Installs ke dalam tipe data integer
playstore[['Reviews', 'Size', 'Installs']] = playstore[['Reviews', 'Size', 'Installs']].astype(int)

@app.route("/")
# dekorator untuk ngerender ke halaman .htmlnya
# This fuction for rendering the table
def index():
    df2 = playstore.copy()

    # Statistik
    # Dataframe top_category dibuat untuk menyimpan frekuensi aplikasi untuk setiap Category. 
    # Gunakan crosstab untuk menghitung frekuensi aplikasi di setiap category kemudian gunakan 'Jumlah'
    # sebagai nama kolom dan urutkan nilai frekuensi dari nilai yang paling banyak. Terakhir reset index dari dataframe top_category 
    top_category = pd.crosstab(index = playstore['Category'], columns = 'count').reset_index().sort_values(by = 'count', ascending = False)
    top_category = top_category.rename(columns={"Category": "Category", "count": "Frequency"})
    # top_category = crosstab
    # Dictionary stats digunakan untuk menyimpan beberapa data yang digunakan untuk menampilkan nilai di value box dan tabel
    stats = {
        # Ini adalah bagian untuk melengkapi konten value box 
        # most category mengambil nama category paling banyak mengacu pada dataframe top_category
        # total mengambil frekuensi/jumlah category paling banyak mengacu pada dataframe top_category
        'most_categories' : top_category.Category[11],
        'total': top_category.Frequency[11],
        # mengambil nilainya: "playstore.___[0]" karena ambil baris paling atas berarti index = 0.
        # total mengambil frekuensi yang poaling banyak.
        # rev_table adalah tabel yang berisi 10 aplikasi yang paling banyak direview oleh pengguna. 
        # Silahkan melakukan agregasi data yang tepat menggunakan groupby untuk menampilkan 10 aplikasi yang diurutkan berdasarkan 
        # jumlah Review pengguna. Tabel yang ditampilkan terdiri dari 4 kolom yaitu nama Category, nama App, total Reviews, dan rata-rata Rating.
        # Agregasi Anda dinilai benar jika hasilnya sama dengan tabel yang terlampir pada file ini
        # rev_table = groupby
        'rev_table' : playstore.groupby(['Category', 'App']).agg({'Reviews' : 'sum', 'Rating' : 'mean'}).sort_values(by = 'Reviews', ascending = False).head(n=10).to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
    }

    ## Bar Plot
    ## Lengkapi tahap agregasi untuk membuat dataframe yang mengelompokkan aplikasi berdasarkan Category
    ## Buatlah bar plot dimana axis x adalah nama Category dan axis y adalah jumlah aplikasi pada setiap kategori, kemudian urutkan dari jumlah terbanyak
    cat_order = playstore.groupby('Category').agg({'Category' : 'count'}).rename({'Category':'Total'}, axis=1).reset_index().sort_values(by = 'Total', ascending = False).head()
    X = cat_order['Category']
    Y = cat_order['Total']
    my_colors = 'rgbkymc'
    # bagian ini digunakan untuk membuat kanvas/figure
    fig = plt.figure(figsize=(8,3),dpi=300)
    fig.add_subplot()
    # bagian ini digunakan untuk membuat bar plot
    plt.barh(X, Y, color = my_colors)
    # bagian ini digunakan untuk menyimpan plot dalam format image.png
    plt.savefig('cat_order.png',bbox_inches="tight") 

    # bagian ini digunakan untuk mengconvert matplotlib png ke base64 agar dapat ditampilkan ke template html
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    # variabel result akan dimasukkan ke dalam parameter di fungsi render_template() agar dapat ditampilkan di 
    # halaman html
    result = str(figdata_png)[2:-1]
    
    ## Scatter Plot
    # Buatlah scatter plot untuk menampilkan hubungan dan persebaran apalikasi dilihat dari Review vs Rating.
    # Ukuran scatter menggambarkan berapa banyak pengguna yang telah menginstall aplikasi 
    X = playstore['Reviews'].values
    Y = playstore['Rating'].values
    area_size = playstore['Installs'].values/10000000
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.scatter(x = X, y = Y, s = area_size, alpha=0.3)
    plt.xlabel('Reviews')
    plt.ylabel('Rating')
    plt.savefig('rev_rat.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result2 = str(figdata_png)[2:-1]

    ## Histogram Size Distribution
    # Buatlah sebuah histogram yang menggambarkan distribusi Size aplikasi dalam satuan Mb(Megabytes) 
    # Histogram yang terbentuk terbagi menjadi 100 bins
    X = (playstore['Size']/1000000).values
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.hist(x = X, bins = 100, density=True, alpha=0.75)
    plt.xlabel('Size')
    plt.ylabel('Frequency')
    plt.savefig('hist_size.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result3 = str(figdata_png)[2:-1]

    ## Buatlah sebuah plot yang menampilkan insight di dalam data     
    content_type = pd.crosstab(index=playstore['Content Rating'], columns= 'count').reset_index().rename(columns={"Content Rating": "Type", "count": "Total"})

    X = content_type['Type']
    Y = content_type['Total'].values
    my_colors = 'rgbkymc'

    explode = (0, 0.1, 0, 0, 0, 0)    

    fig1, ax1 = plt.subplots()
    ax1.pie(Y, explode=explode, labels=X, autopct='%1.1f%%', shadow=True, startangle=90)
    ax1.axis('equal')
    
    plt.savefig('content_type.png', bbox_inches = "tight")
    
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    
    result4 = str(figdata_png)[2:-1]

    # Tambahkan hasil result plot pada fungsi render_template()
    return render_template('index.html', stats=stats, result=result, result2=result2, result3=result3, result4=result4)

if __name__ == "__main__": 
    app.run(debug=True)
