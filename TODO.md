# TODO: Implement General Dataset and Feedback Changes

## 1. Update CONFIG ✅
- Remove HISTORY_FOLDER
- Ensure GENERAL_DATASET = "general_dataset.csv"

## 2. Modify Recommendation Saving Logic
- For guest recommendations: Collect all recommended foods into a single row in GENERAL_DATASET with columns: email, name (NA), sex, height, weight, bmi, tdee, health_goal, recommended_meals (comma-separated), foods_used (NA), goal_progress_rating (NA), progress_description (NA), date ✅
- For user recommendations: Same, but include name from users_df ✅

## 3. Update Feedback Section ("Maoni")
- Change to show eligible recommendations (date >= 14 days ago, foods_used is NA)
- For each eligible row, show form: multiselect eaten foods from recommended_meals.split(','), rating 0-4, description text
- Update the row with selected foods, rating, description

## 4. Add Email Reminder Logic
- On app load, check for rows where date + 14 days <= now and feedback not filled, send email with form link or instructions to fill feedback in app

## 5. Update History Display
- Load from GENERAL_DATASET, filter by user email, show relevant columns

## 6. Update Admin Download
- Download GENERAL_DATASET instead of per-goal files

## 7. Remove Old Per-Goal Saving
- Remove code that saves to HISTORY_FOLDER per goal

## 8. Prevent Guest Recommendations ✅
- Modify guest expander to show info message directing to login/register instead of generating recommendations
- Remove recommendation generation, saving, and email reminder info for guests
