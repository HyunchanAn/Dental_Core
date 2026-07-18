def calculate_iou(boxA, boxB):
    """
    단순 교차 영역 면적 비율 (Intersection over Area of Lesion)
    """
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    return interArea / float(boxAArea) if boxAArea > 0 else 0

def map_lesions_to_fdi(caries_data, tooth_roi_data):
    """
    병소 BBox와 치아 BBox를 기하학적으로 매핑합니다.
    """
    mapped = []
    for i, lesion_box in enumerate(caries_data['boxes']):
        lesion_label = caries_data['labels'][i]
        best_iou = 0
        best_fdi = "Unknown"
        
        # 모든 치아 박스와 비교하여 가장 겹침(IoU)이 큰 치아 번호를 할당
        for j, tooth_box in enumerate(tooth_roi_data['boxes']):
            fdi = tooth_roi_data['fdi_labels'][j]
            iou = calculate_iou(lesion_box, tooth_box)
            if iou > best_iou:
                best_iou = iou
                best_fdi = fdi
                
        mapped.append({
            'lesion_type': lesion_label,
            'box': lesion_box,
            'fdi': best_fdi
        })
        
    return mapped
