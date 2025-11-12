# utils/matching_algorithm.py
from models.user import UserProfile
from utils.geolocation import calculate_distance


def find_potential_matches(user, virtual_partner=False, max_results=20):
    """
    根据用户信息寻找潜在匹配对象
    """
    user_profile = user.profile

    # 排除已经匹配或发送过请求的用户
    existing_matches_user_ids = [m.matched_user_id for m in user.sent_matches if m.status != 'rejected']
    existing_matches_user_ids.extend([m.user_id for m in user.received_matches if m.status != 'rejected'])

    # 查询潜在匹配用户
    query = UserProfile.query.filter(
        UserProfile.user_id != user.id,
        UserProfile.user_id.notin_(existing_matches_user_ids),
        UserProfile.profile_visible == True
    )

    potential_profiles = query.limit(max_results).all()

    matches_with_score = []
    for profile in potential_profiles:
        score = calculate_match_score(user_profile, profile)

        match_data = profile.to_dict()
        match_data['match_score'] = score

        # 计算距离（如果位置可见）
        if (user_profile.latitude and user_profile.longitude and
                profile.latitude and profile.longitude):
            distance = calculate_distance(
                user_profile.latitude, user_profile.longitude,
                profile.latitude, profile.longitude
            )
            match_data['distance'] = round(distance, 2)

        matches_with_score.append(match_data)

    # 按匹配度排序
    matches_with_score.sort(key=lambda x: x['match_score'], reverse=True)
    return matches_with_score


def calculate_match_score(profile1, profile2):
    """
    计算两个用户资料的匹配度
    """
    score = 0

    # 年龄匹配（年龄差越小分数越高）
    if profile1.age and profile2.age:
        age_diff = abs(profile1.age - profile2.age)
        if age_diff <= 5:
            score += 30
        elif age_diff <= 10:
            score += 20
        elif age_diff <= 15:
            score += 10

    # 地理位置匹配（距离越近分数越高）
    if (profile1.latitude and profile1.longitude and
            profile2.latitude and profile2.longitude):
        distance = calculate_distance(
            profile1.latitude, profile1.longitude,
            profile2.latitude, profile2.longitude
        )
        if distance <= 10:  # 10公里内
            score += 40
        elif distance <= 50:  # 50公里内
            score += 20
        elif distance <= 100:  # 100公里内
            score += 10

    # 确保基础分
    if score == 0:
        score = 20  # 基础匹配分

    return min(score, 100)