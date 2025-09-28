import matplotlib.pyplot as plt


def SCORE_edit_chart_pkl3(fig):
    # with open('./data/eval2/enhanced_response_analysis.pkl', 'rb') as f:
    #     fig = pickle.load(f)


    # ------- Trục chứa thời gian phản hồi -------
    ax1 = fig.axes[0]  

    # print list label
    for i, annotation in enumerate(ax1.texts):
        print(f"{i}: {annotation.get_text()}, pos={annotation.get_position()}")
    

    for annotation in ax1.texts:
        if annotation.get_text() == "10.8":
            x, y = annotation.get_position()
            annotation.set_position((x, y - 40))  
        if annotation.get_text() == "15.7":
            x, y = annotation.get_position()
            annotation.set_position((x, y - 28))  
        if annotation.get_text() == "16.7":
            x, y = annotation.get_position()
            annotation.set_position((x, y - 25))  
        if annotation.get_text() == "19.6":
            x, y = annotation.get_position()
            annotation.set_position((x, y - 25))  
        if annotation.get_text() == "22.5":
            x, y = annotation.get_position()
            annotation.set_position((x, y - 28))  
        if annotation.get_text() == "25.8":
            x, y = annotation.get_position()
            annotation.set_position((x, y - 30))  
        if annotation.get_text() == "30.7":
            x, y = annotation.get_position()
            annotation.set_position((x, y - 30))  
        if annotation.get_text() == "33.5":
            x, y = annotation.get_position()
            annotation.set_position((x, y - 30))  
        if annotation.get_text() == "38.9":
            x, y = annotation.get_position()
            annotation.set_position((x, y - 30))  
        if annotation.get_text() == "42.1":
            x, y = annotation.get_position()
            annotation.set_position((x, y - 30)) 
        if annotation.get_text() == "47.9":
            x, y = annotation.get_position()
            annotation.set_position((x, y - 30)) 
        if annotation.get_text() == "51.7":
            x, y = annotation.get_position()
            annotation.set_position((x, y - 30)) 
        if annotation.get_text() == "54.9":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 5)) 
        if annotation.get_text() == "57.7":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 5)) 
        if annotation.get_text() == "61.8":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 5)) 
    

    
    
            
            
    # ------- Trục chứa chất lượng phản hồi -------
    ax2 = fig.axes[1]

    # print list label
    for annotation in ax2.texts:
        if annotation.get_text() == "6.32":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 40))

        if annotation.get_text() == "6.69":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 40))  
            
        if annotation.get_text() == "6.80":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 40))  
        
        if annotation.get_text() == "6.76":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 40))

        if annotation.get_text() == "6.79":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 40)) 
            
        if annotation.get_text() == "6.83":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 40))
        if annotation.get_text() == "6.98":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 40))
        if annotation.get_text() == "7.08":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 40))
        if annotation.get_text() == "6.94":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 40))
        if annotation.get_text() == "7.12":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 40))
        if annotation.get_text() == "7.05":
            x, y = annotation.get_position()
            annotation.set_position((x, y - 5))
            
    for annotation in ax2.texts:
        if annotation.get_text() == "7.00":
            x, y = annotation.get_position()
            annotation.set_position((x, y + 40))
            break
    i = 0
    for annotation in ax2.texts:
        if annotation.get_text() == "7.00":
            i += 1
        if annotation.get_text() == "7.00" and i == 2:
            x, y = annotation.get_position()
            annotation.set_position((x, y + 5))
            break
        



    plt.savefig(f'./data/eval3/SCORE_topk_affect.png', dpi=500, bbox_inches='tight')
    # with open('./data/eval2/enhanced_response_analysis_adjusted.pkl', 'wb') as f:
    #     pickle.dump(fig, f)

    print("✅ Đã chỉnh sửa nhãn thành công và lưu lại ảnh mới.")